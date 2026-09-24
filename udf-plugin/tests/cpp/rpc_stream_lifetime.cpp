#include <dlfcn.h>

#include <chrono>
#include <condition_variable>
#include <iostream>
#include <memory>
#include <mutex>
#include <string>
#include <thread>

#include <grpcpp/grpcpp.h>

#include "generic_client_factory.h"
#include "generic_record_impl.h"
#include "udf_stream.grpc.pb.h"

namespace {

class blocking_stream_service : public StreamTestService::Service {
public:
    grpc::Status stream_test_one(
        grpc::ServerContext* context,
        AA const* request,
        grpc::ServerWriter<BigintValue>* writer
    ) override {
        (void) request;
        (void) writer;

        {
            std::lock_guard lk(mutex_);
            started_ = true;
        }
        cv_.notify_all();

        while(! context->IsCancelled()) {
            std::this_thread::sleep_for(std::chrono::milliseconds(10));
        }

        {
            std::lock_guard lk(mutex_);
            cancelled_ = true;
            finished_ = true;
        }
        cv_.notify_all();

        return grpc::Status(grpc::StatusCode::CANCELLED, "client cancelled");
    }

    bool wait_started(std::chrono::milliseconds timeout) { return wait_until(timeout, [&] { return started_; }); }

    bool wait_cancelled(std::chrono::milliseconds timeout) { return wait_until(timeout, [&] { return cancelled_; }); }

    bool wait_finished(std::chrono::milliseconds timeout) { return wait_until(timeout, [&] { return finished_; }); }

private:
    template<class Predicate>
    bool wait_until(std::chrono::milliseconds timeout, Predicate pred) {
        std::unique_lock lk(mutex_);
        return cv_.wait_for(lk, timeout, pred);
    }

    std::mutex mutex_;
    std::condition_variable cv_;
    bool started_{false};
    bool cancelled_{false};
    bool finished_{false};
};

template<class T>
T load_symbol(void* handle, char const* name) {
    dlerror();
    auto* symbol = dlsym(handle, name);
    if(symbol == nullptr) {
        char const* error = dlerror();
        std::cerr << "dlsym failed for " << name << ": " << (error != nullptr ? error : "(unknown)") << '\n';
        return nullptr;
    }
    return reinterpret_cast<T>(symbol);
}

}  // namespace

int main(int argc, char** argv) {
    if(argc != 2) {
        std::cerr << "usage: rpc_stream_lifetime <plugin-so>\n";
        return 1;
    }

    blocking_stream_service service;
    grpc::ServerBuilder builder;
    int selected_port = 0;
    builder.AddListeningPort("127.0.0.1:0", grpc::InsecureServerCredentials(), &selected_port);
    builder.RegisterService(&service);
    auto server = builder.BuildAndStart();
    if(! server || selected_port == 0) {
        std::cerr << "failed to start blocking gRPC server\n";
        return 2;
    }

    void* handle = dlopen(argv[1], RTLD_NOW | RTLD_GLOBAL);
    if(handle == nullptr) {
        char const* error = dlerror();
        std::cerr << "dlopen failed: " << (error != nullptr ? error : "(unknown)") << '\n';
        server->Shutdown();
        return 3;
    }

    using create_factory_func = plugin::udf::generic_client_factory* (*)(char const*);
    using destroy_factory_func = void (*)(plugin::udf::generic_client_factory*);
    using destroy_client_func = void (*)(plugin::udf::generic_client*);

    auto* create_factory = load_symbol<create_factory_func>(handle, "tsurugi_create_generic_client_factory");
    auto* destroy_factory = load_symbol<destroy_factory_func>(handle, "tsurugi_destroy_generic_client_factory");
    auto* destroy_client = load_symbol<destroy_client_func>(handle, "tsurugi_destroy_generic_client");
    if(create_factory == nullptr || destroy_factory == nullptr || destroy_client == nullptr) {
        server->Shutdown();
        dlclose(handle);
        return 4;
    }

    std::unique_ptr<plugin::udf::generic_client_factory, destroy_factory_func> factory(
        create_factory("StreamTestService"),
        destroy_factory
    );
    // Keep this lifetime test focused while the generated factory still accepts the legacy service name.
    if(! factory) {
        factory.reset(create_factory("Greeter"));
    }
    if(! factory) {
        std::cerr << "failed to create generic client factory\n";
        server->Shutdown();
        dlclose(handle);
        return 5;
    }

    auto channel = grpc::CreateChannel(
        "127.0.0.1:" + std::to_string(selected_port),
        grpc::InsecureChannelCredentials()
    );
    std::unique_ptr<plugin::udf::generic_client, destroy_client_func> client(factory->create(channel), destroy_client);
    if(! client) {
        std::cerr << "failed to create generic client\n";
        server->Shutdown();
        factory.reset();
        dlclose(handle);
        return 6;
    }

    plugin::udf::generic_record_impl request;
    request.add_int8(123);
    auto context = std::make_unique<plugin::udf::generic_client_context>();
    auto stream = client->call_server_streaming_async(std::move(context), {0, 0}, request);
    if(! stream) {
        std::cerr << "call_server_streaming_async returned nullptr\n";
        server->Shutdown();
        client.reset();
        factory.reset();
        dlclose(handle);
        return 7;
    }

    client.reset();

    if(! service.wait_started(std::chrono::seconds(5))) {
        std::cerr << "streaming RPC did not become active\n";
        stream.reset();
        server->Shutdown();
        factory.reset();
        dlclose(handle);
        return 8;
    }

    // close() cancels and joins the client worker before returning, making the later dlclose safe.
    stream.reset();

    if(! service.wait_cancelled(std::chrono::seconds(5))) {
        std::cerr << "stream destruction did not cancel the active RPC\n";
        server->Shutdown();
        factory.reset();
        dlclose(handle);
        return 9;
    }

    if(! service.wait_finished(std::chrono::seconds(5))) {
        std::cerr << "server handler did not finish after cancellation\n";
        server->Shutdown();
        factory.reset();
        dlclose(handle);
        return 10;
    }

    server->Shutdown();
    factory.reset();
    dlclose(handle);
    return 0;
}
