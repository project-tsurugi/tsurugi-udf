#include <iostream>
#include <memory>
#include <string>
#include <boost/property_tree/ini_parser.hpp>
#include <boost/property_tree/ptree.hpp>

#include "complex_types.pb.h"
#include "nested_test.grpc.pb.h"
#include "nested_test.pb.h"

#include <grpcpp/grpcpp.h>

using grpc::Server;
using grpc::ServerBuilder;
using grpc::ServerContext;
using grpc::Status;

class NestedImpl final : public Nested::Service {
    Status NestedHello(ServerContext* context, const SimpleValue* request, SimpleValue* reply) override {
        std::cout << "[NestedHello]" << std::endl;
        std::cout << "value :" << request->value() << std::endl;
        reply->set_value("hello" + request->value());
        return Status::OK;
    }
    Status DecimalOne(ServerContext* context, const DecimalWrap* request, SimpleValue* reply) override {
        std::cout << "[DecimalOne]" << std::endl;
        std::cout << " unscaled_value : " << request->dec().unscaled_value()
                  << "\n exponent: " << request->dec().exponent() << std::endl;

        reply->set_value("DecimalOne received");
        return Status::OK;
    }

    Status DecimalTwo(ServerContext* context, const AddDecimal* request, SimpleValue* reply) override {
        std::cout << "[DecimalTwo]" << std::endl;
        std::cout << "i32: " << request->i32() << std::endl;
        std::cout << "unscaled_value : " << request->dec().unscaled_value()
                  << ", exponent: " << request->dec().exponent() << std::endl;

        reply->set_value("DecimalTwo received");
        return Status::OK;
    }
    Status DateOne(ServerContext* context, const WrapDate* request, WrapDate* reply) override {
        std::cout << "[DateOne]" << std::endl;
        std::cout << " days : " << request->value().days() << std::endl;
        auto* v = reply->mutable_value();
        v->set_days(request->value().days());
        return Status::OK;
    }
    Status DateTwo(ServerContext* context, const AddDate* request, WrapDate* reply) override {
        std::cout << "[DateTwo]" << std::endl;
        std::cout << " value : " << request->value() << std::endl;
        std::cout << " days  : " << request->dec().days() << std::endl;
        auto* v = reply->mutable_value();
        v->set_days(request->dec().days());
        return Status::OK;
    }
    Status LocalTimeOne(ServerContext* context, const WrapLocalTime* request, WrapLocalTime* reply) override {
        std::cout << "[LocalTimeOne]" << std::endl;
        std::cout << " nanos : " << request->lt().nanos() << std::endl;
        auto* v = reply->mutable_lt();
        v->set_nanos(request->lt().nanos());
        return Status::OK;
    }
    Status LocalTimeTwo(ServerContext* context, const AddLocalTime* request, WrapLocalTime* reply) override {
        std::cout << "[LocalTimeTwo]" << std::endl;
        std::cout << " value : " << request->value() << std::endl;
        std::cout << " dec->nanos() : " << request->dec().nanos() << std::endl;
        std::cout << " vv : " << request->vv() << std::endl;
        auto* v = reply->mutable_lt();
        v->set_nanos(request->dec().nanos());
        return Status::OK;
    }
    Status
    LocalDatetimeOne(ServerContext* context, const WrapLocalDatetime* request, WrapLocalDatetime* reply) override {
        std::cout << "[LocalDatetimeOne]" << std::endl;
        std::cout << " offset_seconds : " << request->ld().offset_seconds() << std::endl;
        std::cout << " nano_adjustment : " << request->ld().nano_adjustment() << std::endl;
        auto* v = reply->mutable_ld();
        v->set_offset_seconds(request->ld().offset_seconds());
        v->set_nano_adjustment(request->ld().nano_adjustment());
        return Status::OK;
    }
    Status
    LocalDatetimeTwo(ServerContext* context, const AddLocalDatetime* request, WrapLocalDatetime* reply) override {
        std::cout << "[LocalDatetimeTwo]" << std::endl;
        std::cout << " dec->offset_seconds() : " << request->dec().offset_seconds() << std::endl;
        std::cout << " dec->nano_adjustment() : " << request->dec().nano_adjustment() << std::endl;
        std::cout << " vv() : " << request->vv() << std::endl;
        auto* v = reply->mutable_ld();
        v->set_offset_seconds(request->dec().offset_seconds());
        v->set_nano_adjustment(request->dec().nano_adjustment());
        return Status::OK;
    }

    Status
    OffsetDatetimeOne(ServerContext* context, const WrapOffsetDatetime* request, WrapOffsetDatetime* reply) override {
        std::cout << "[OffsetDatetimeOne]" << std::endl;
        std::cout << " offset_seconds : " << request->od().offset_seconds() << std::endl;
        std::cout << " nano_adjustment : " << request->od().nano_adjustment() << std::endl;
        std::cout << " time_zone_offset : " << request->od().time_zone_offset() << std::endl;
        auto* v = reply->mutable_od();
        v->set_offset_seconds(request->od().offset_seconds());
        v->set_nano_adjustment(request->od().nano_adjustment());
        v->set_time_zone_offset(request->od().time_zone_offset());
        return Status::OK;
    }
    Status
    BlobReferenceOne(ServerContext* context, const WrapBlobReference* request, WrapBlobReference* reply) override {
        std::cout << "[BlobReferenceOne]" << std::endl;
        std::cout << " storage_id : " << request->br().storage_id() << std::endl;
        std::cout << " object_id : " << request->br().object_id() << std::endl;
        std::cout << " tag : " << request->br().tag() << std::endl;
        auto* v = reply->mutable_br();
        v->set_storage_id(request->br().storage_id());
        v->set_object_id(request->br().object_id());
        v->set_tag(request->br().tag());
        return Status::OK;
    }
    Status
    ClobReferenceOne(ServerContext* context, const WrapClobReference* request, WrapClobReference* reply) override {
        std::cout << "[ClobReferenceOne]" << std::endl;
        std::cout << " storage_id : " << request->cr().storage_id() << std::endl;
        std::cout << " object_id : " << request->cr().object_id() << std::endl;
        std::cout << " tag : " << request->cr().tag() << std::endl;
        auto* v = reply->mutable_cr();
        v->set_storage_id(request->cr().storage_id());
        v->set_object_id(request->cr().object_id());
        v->set_tag(request->cr().tag());
        return Status::OK;
    }
};

void RunServer(const std::string& server_address, const std::string& secure) {
    NestedImpl test_service;


    grpc::ServerBuilder builder;

    if(secure == "false") {
        builder.AddListeningPort(server_address, grpc::InsecureServerCredentials());
    } else {
        std::cerr << "[WARN] Unsupported secure: " << secure << " (falling back to false)\n";
        builder.AddListeningPort(server_address, grpc::InsecureServerCredentials());
    }

    builder.RegisterService(&test_service);

    std::unique_ptr<grpc::Server> server(builder.BuildAndStart());
    std::cout << "Server listening on " << server_address << std::endl;

    server->Wait();
}

int main(int argc, char** argv) {
    std::string server_address = "0.0.0.0:50051";
    std::string secure = "false";

    if(argc >= 2) {
        std::string ini_file = argv[1];
        boost::property_tree::ptree pt;
        try {
            boost::property_tree::ini_parser::read_ini(ini_file, pt);
            server_address = pt.get<std::string>("udf.endpoint", server_address);
            secure = pt.get<std::string>("udf.secure", secure);
            std::cout << "[INFO] Loaded gRPC settings from " << ini_file << "\n";
        } catch(const boost::property_tree::ini_parser_error& e) {
            std::cerr << "[WARN] Failed to read ini file '" << ini_file << "': " << e.what() << "\n";
            std::cerr << "[INFO] Using default gRPC settings\n";
        }
    } else {
        std::cout << "[INFO] No ini file specified. Using default gRPC settings\n";
    }

    RunServer(server_address, secure);
    return 0;
}
