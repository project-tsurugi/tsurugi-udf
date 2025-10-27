#include <cstdint>
#include <iostream>
#include <memory>
#include <string>
#include <boost/property_tree/ini_parser.hpp>
#include <boost/property_tree/ptree.hpp>

#include "test_all.grpc.pb.h"
#include "test_all.pb.h"

#include <grpcpp/grpcpp.h>
using grpc::Server;
using grpc::ServerBuilder;
using grpc::ServerContext;
using grpc::Status;

class TestServiceImpl final : public TestService::Service {

    // @see https://protobuf.dev/programming-guides/proto3/#scalar
    Status EchoInt32(ServerContext* context, const Int32Request* request, Int32Reply* reply) override {
        int32_t value = 32;
        std::cerr << "EchoInt32" << std::endl;
        std::cerr << "  value: " << value << std::endl;
        std::cerr << "  request->value():" << request->value() << std::endl;
        reply->set_result(value + request->value());
        return Status::OK;
    }
    Status EchoUInt32(ServerContext* context, const UInt32Request* request, UInt32Reply* reply) override {
        uint32_t value = 32;
        std::cerr << "EchoUInt32" << std::endl;
        std::cerr << "  value: " << value << std::endl;
        std::cerr << "  request->value():" << request->value() << std::endl;
        reply->set_result(value + request->value());
        reply->set_result(value + request->value());
        return Status::OK;
    }
    // sint32	int32_t
    Status EchoSInt32(ServerContext* context, const SInt32Request* request, SInt32Reply* reply) override {
        int32_t value = 32;
        std::cerr << "EchoSInt32" << std::endl;
        std::cerr << "  value: " << value << std::endl;
        std::cerr << "  request->value():" << request->value() << std::endl;
        reply->set_result(value + request->value());
        return Status::OK;
    }
    // fixed32	uint32_t
    Status EchoFixed32(ServerContext* context, const Fixed32Request* request, Fixed32Reply* reply) override {
        uint32_t value = 32;

        std::cerr << "EchoFixed32" << std::endl;
        std::cerr << "  value: " << value << std::endl;
        std::cerr << "  request->value():" << request->value() << std::endl;
        reply->set_result(value + request->value());
        return Status::OK;
    }
    // sfixed32	int32_t
    Status EchoSFixed32(ServerContext* context, const SFixed32Request* request, SFixed32Reply* reply) override {
        int32_t value = 32;
        std::cerr << "EchoSFixed32" << std::endl;
        std::cerr << "  value: " << value << std::endl;
        std::cerr << "  request->value():" << request->value() << std::endl;
        reply->set_result(value + request->value());
        return Status::OK;
    }
    Status EchoInt64(ServerContext* context, const Int64Request* request, Int64Reply* reply) override {
        int64_t value = 64;
        std::cerr << "EchoInt64" << std::endl;
        std::cerr << "  value: " << value << std::endl;
        std::cerr << "  request->value():" << request->value() << std::endl;
        reply->set_result(value + request->value());
        return Status::OK;
    }
    Status EchoUInt64(ServerContext* context, const UInt64Request* request, UInt64Reply* reply) override {
        uint64_t value = 64;
        std::cerr << "EchoUInt64" << std::endl;
        std::cerr << "  value: " << value << std::endl;
        std::cerr << "  request->value():" << request->value() << std::endl;
        reply->set_result(value + request->value());
        return Status::OK;
    }
    // sint64	int64_t
    Status EchoSInt64(ServerContext* context, const SInt64Request* request, SInt64Reply* reply) override {
        int64_t value = 64;
        std::cerr << "EchoSInt64" << std::endl;
        std::cerr << "  value: " << value << std::endl;
        std::cerr << "  request->value():" << request->value() << std::endl;
        reply->set_result(value + request->value());
        return Status::OK;
    }
    // fixed64	uint64_t
    Status EchoFixed64(ServerContext* context, const Fixed64Request* request, Fixed64Reply* reply) override {
        uint64_t value = 64;
        std::cerr << "EchoFixed64" << std::endl;
        std::cerr << "  value: " << value << std::endl;
        std::cerr << "  request->value():" << request->value() << std::endl;
        reply->set_result(value + request->value());
        return Status::OK;
    }
    // sfixed64	int64_t
    Status EchoSFixed64(ServerContext* context, const SFixed64Request* request, SFixed64Reply* reply) override {
        int64_t value = 64;
        std::cerr << "EchoSFixed64" << std::endl;
        std::cerr << "  value: " << value << std::endl;
        std::cerr << "  request->value():" << request->value() << std::endl;
        reply->set_result(value + request->value());
        return Status::OK;
    }
    Status EchoFloat(ServerContext* context, const FloatRequest* request, FloatReply* reply) override {
        float value = 3.14;
        std::cerr << "EchoFloat" << std::endl;
        std::cerr << "  value: " << value << std::endl;
        std::cerr << "  request->value():" << request->value() << std::endl;
        reply->set_result(value + request->value());
        return Status::OK;
    }
    Status EchoDouble(ServerContext* context, const DoubleRequest* request, DoubleReply* reply) override {
        double value = 2.718;
        std::cerr << "EchoDouble" << std::endl;
        std::cerr << "  value: " << value << std::endl;
        std::cerr << "  request->value():" << request->value() << std::endl;
        reply->set_result(value + request->value());
        return Status::OK;
    }
    Status EchoString(ServerContext* context, const StringRequest* request, StringReply* reply) override {
        std::string prefix("Hello ");
        std::cerr << "EchoString" << std::endl;
        std::cerr << "  prefix: " << prefix << std::endl;
        std::cerr << "  request->value():" << request->value() << std::endl;
        reply->set_result(prefix + request->value());
        return Status::OK;
    }
    Status EchoBytes(ServerContext* context, const BytesRequest* request, BytesReply* reply) override {
        std::string prefix("Bytes: ");
        std::cerr << "EchoBytes" << std::endl;
        std::cerr << "  prefix: " << prefix << std::endl;
        std::cerr << "  request->value():" << request->value() << std::endl;
        reply->set_result(prefix + request->value());
        return Status::OK;
    }
    Status EchoBool(ServerContext* context, const BoolRequest* request, BoolReply* reply) override {
        std::cerr << "EchoBool" << std::endl;
        std::cerr << "  request->value():" << request->value() << std::endl;
        reply->set_result(! request->value());
        return Status::OK;
    }
    Status
    ConcatInt32String(ServerContext* context, const Int32StringRequest* request, Int32StringReply* reply) override {
        std::cerr << "ConcatInt32String" << std::endl;
        std::cerr << "  request->id():" << request->id() << std::endl;
        std::cerr << "  request->name():" << request->name() << std::endl;
        reply->set_message("ID: " + std::to_string(request->id()) + ", Name: " + request->name());
        return Status::OK;
    }
    Status
    ConcatStringInt32(ServerContext* context, const StringInt32Request* request, StringInt32Reply* reply) override {
        std::cerr << "ConcatStringInt32" << std::endl;
        std::cerr << "  request->name():" << request->name() << std::endl;
        std::cerr << "  request->id():" << request->id() << std::endl;
        reply->set_message("ID: " + std::to_string(request->id()) + ", Name: " + request->name());
        return Status::OK;
    }
    Status SumInt32Int64(ServerContext* context, const Int32Int64Request* request, Int32Int64Reply* reply) override {
        std::cerr << "SumInt32Int64" << std::endl;
        std::cerr << "  request->small():" << request->small() << std::endl;
        std::cerr << "  request->big():" << request->big() << std::endl;
        reply->set_sum(request->small() + request->big());
        return Status::OK;
    }
    Status
    MultiplyFloatDouble(ServerContext* context, const FloatDoubleRequest* request, FloatDoubleReply* reply) override {
        std::cerr << "MultiplyFloatDouble" << std::endl;
        std::cerr << "  request->fval():" << request->fval() << std::endl;
        std::cerr << "  request->dval():" << request->dval() << std::endl;
        reply->set_result(request->fval() * request->dval());
        return Status::OK;
    }
    Status
    CombineStringBytes(ServerContext* context, const StringBytesRequest* request, StringBytesReply* reply) override {
        std::cerr << "CombineStringBytes" << std::endl;
        std::cerr << "  request->text():" << request->text() << std::endl;
        std::cerr << "  request->blob():" << request->blob() << std::endl;
        reply->set_combined(request->text() + request->blob());
        return Status::OK;
    }
    Status
    FormatBoolInt32String(ServerContext* context, const BoolInt32StringRequest* request, BoolInt32StringReply* reply)
        override {
        std::cerr << "FormatBoolInt32String" << std::endl;
        std::cerr << "  request->flag():" << request->flag() << std::endl;
        std::cerr << "  request->count():" << request->count() << std::endl;
        std::cerr << "  request->label():" << request->label() << std::endl;
        reply->set_message(
            "Flag: " + std::to_string(request->flag()) + ", Count: " + std::to_string(request->count()) +
            ", Label: " + request->label()
        );
        return Status::OK;
    }
    Status UseAllTypes(ServerContext* context, const AllTypesRequest* request, AllTypesReply* reply) override {
        std::cerr << "UseAllTypes" << std::endl;
        std::cerr << "  request->i32():" << request->i32() << std::endl;
        std::cerr << "  request->i64():" << request->i64() << std::endl;
        std::cerr << "  request->ui32():" << request->ui32() << std::endl;
        std::cerr << "  request->ui64():" << request->ui64() << std::endl;
        std::cerr << "  request->si32():" << request->si32() << std::endl;
        std::cerr << "  request->si64():" << request->si64() << std::endl;
        std::cerr << "  request->fi32():" << request->fi32() << std::endl;
        std::cerr << "  request->fi64():" << request->fi64() << std::endl;
        std::cerr << "  request->sfi32():" << request->sfi32() << std::endl;
        std::cerr << "  request->sfi64():" << request->sfi64() << std::endl;
        std::cerr << "  request->f32():" << request->f32() << std::endl;
        std::cerr << "  request->f64():" << request->f64() << std::endl;
        std::cerr << "  request->text():" << request->text() << std::endl;
        std::cerr << "  request->blob():" << request->blob() << std::endl;
        std::cerr << "  request->flag():" << request->flag() << std::endl;
        reply->set_summary(
            "i32: " + std::to_string(request->i32()) + ", i64: " + std::to_string(request->i64()) +
            ", ui32: " + std::to_string(request->ui32()) + ", ui64: " + std::to_string(request->ui64()) +
            ", si32: " + std::to_string(request->si32()) + ", si64: " + std::to_string(request->si64()) +
            ", fi32: " + std::to_string(request->fi32()) + ", fi64: " + std::to_string(request->fi64()) +
            ", sfi32: " + std::to_string(request->sfi32()) + ", sfi64: " + std::to_string(request->sfi64()) +
            ", f32: " + std::to_string(request->f32()) + ", f64: " + std::to_string(request->f64()) +
            ", text: " + request->text() + ", blob size: " + std::to_string(request->blob().size()) +
            ", flag: " + std::to_string(request->flag())
        );
        return Status::OK;
    }
};

void RunServer(const std::string& server_address, const std::string& credentials) {
    TestServiceImpl test_service;

    grpc::ServerBuilder builder;

    if(credentials == "insecure") {
        builder.AddListeningPort(server_address, grpc::InsecureServerCredentials());
    } else {
        std::cerr << "[WARN] Unsupported credentials: " << credentials << " (falling back to insecure)\n";
        builder.AddListeningPort(server_address, grpc::InsecureServerCredentials());
    }

    builder.RegisterService(&test_service);

    std::unique_ptr<grpc::Server> server(builder.BuildAndStart());
    std::cout << "Server listening on " << server_address << std::endl;

    server->Wait();
}

int main(int argc, char** argv) {
    std::string server_address = "0.0.0.0:50051";
    std::string credentials = "insecure";

    if(argc >= 2) {
        std::string ini_file = argv[1];
        boost::property_tree::ptree pt;
        try {
            boost::property_tree::ini_parser::read_ini(ini_file, pt);
            server_address = pt.get<std::string>("udf.url", server_address);
            credentials = pt.get<std::string>("udf.credentials", credentials);
            std::cout << "[INFO] Loaded gRPC settings from " << ini_file << "\n";
        } catch(const boost::property_tree::ini_parser_error& e) {
            std::cerr << "[WARN] Failed to read ini file '" << ini_file << "': " << e.what() << "\n";
            std::cerr << "[INFO] Using default gRPC settings\n";
        }
    } else {
        std::cout << "[INFO] No ini file specified. Using default gRPC settings\n";
    }

    RunServer(server_address, credentials);
    return 0;
}
