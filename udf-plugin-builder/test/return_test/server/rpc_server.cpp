#include <iostream>
#include <memory>
#include <string>
#include <boost/property_tree/ini_parser.hpp>
#include <boost/property_tree/ptree.hpp>

#include "return.grpc.pb.h"
#include "return.pb.h"
#include "tsurugi_types.pb.h"

#include <grpcpp/grpcpp.h>

using grpc::Server;
using grpc::ServerBuilder;
using grpc::ServerContext;
using grpc::Status;

class RecServiceImpl final : public Rec::Service {
    Status inc_date(ServerContext* context, const DateMessage* request, DateMessage* reply) override {
        std::cerr << "inc_date" << std::endl;
        std::cerr << "  request->date().days(): " << request->date().days() << std::endl;
        auto* v = reply->mutable_date();
        v->set_days(request->date().days() + 1);
        return Status::OK;
    }
    Status inc_decimal(ServerContext* context, const DecimalMessage* request, DecimalMessage* reply) override {
        std::cerr << "inc_decimal" << std::endl;
        std::cerr << "  request->value().unscaled_value(): " << request->value().unscaled_value() << std::endl;
        std::cerr << "  request->value().exponent(): " << request->value().exponent() << std::endl;
        auto* v = reply->mutable_value();
        v->set_unscaled_value(request->value().unscaled_value());
        v->set_exponent(request->value().exponent() + 1);
        return Status::OK;
    }
    Status inc_local_time(ServerContext* context, const LocalTimeMessage* request, LocalTimeMessage* reply) override {
        std::cerr << "inc_local_time" << std::endl;
        std::cerr << "  request->time().nanos(): " << request->time().nanos() << std::endl;
        auto* v = reply->mutable_time();
        v->set_nanos(request->time().nanos() + 1);
        return Status::OK;
    }
    Status inc_local_date_time(ServerContext* context, const LocalDatetimeMessage* request, LocalDatetimeMessage* reply)
        override {
        std::cerr << "inc_local_date_time" << std::endl;
        std::cerr << "  request->ldm().offset_seconds(): " << request->ldm().offset_seconds() << std::endl;
        std::cerr << "  request->ldm().nano_adjustment(): " << request->ldm().nano_adjustment() << std::endl;
        auto* v = reply->mutable_ldm();
        v->set_offset_seconds(request->ldm().offset_seconds() + 1);
        v->set_nano_adjustment(request->ldm().nano_adjustment() + 1);
        return Status::OK;
    }
    Status
    inc_offset_date_time(ServerContext* context, const OffsetDatetimeMessage* request, OffsetDatetimeMessage* reply)
        override {
        std::cerr << "inc_offset_date_time" << std::endl;
        std::cerr << "  request->od().offset_seconds(): " << request->od().offset_seconds() << std::endl;
        std::cerr << "  request->od().nano_adjustment(): " << request->od().nano_adjustment() << std::endl;
        std::cerr << "  request->od().time_zone_offset(): " << request->od().time_zone_offset() << std::endl;
        auto* v = reply->mutable_od();
        v->set_offset_seconds(request->od().offset_seconds() + 1);
        v->set_nano_adjustment(request->od().nano_adjustment() + 1);
        v->set_time_zone_offset(request->od().time_zone_offset() + 1);
        return Status::OK;
    }
    Status inc_blob_referece(ServerContext* context, const BlobReferenceMessage* request, BlobReferenceMessage* reply)
        override {
        std::cerr << "inc_blob_referece" << std::endl;
        std::cerr << "  request->br().storage_id(): " << request->br().storage_id() << std::endl;
        std::cerr << "  request->br().object_id(): " << request->br().object_id() << std::endl;
        std::cerr << "  request->br().tag(): " << request->br().tag() << std::endl;
        auto* v = reply->mutable_br();
        v->set_storage_id(request->br().storage_id() + 1);
        v->set_object_id(request->br().object_id() + 1);
        v->set_tag(request->br().tag() + 1);
        return Status::OK;
    }
    Status inc_clob_referece(ServerContext* context, const ClobReferenceMessage* request, ClobReferenceMessage* reply)
        override {
        std::cerr << "inc_clob_referece" << std::endl;
        std::cerr << "  request->cr().storage_id(): " << request->cr().storage_id() << std::endl;
        std::cerr << "  request->cr().object_id(): " << request->cr().object_id() << std::endl;
        std::cerr << "  request->cr().tag(): " << request->cr().tag() << std::endl;
        auto* v = reply->mutable_cr();
        v->set_storage_id(request->cr().storage_id() + 1);
        v->set_object_id(request->cr().object_id() + 1);
        v->set_tag(request->cr().tag() + 1);
        return Status::OK;
    }
};

void RunServer(const std::string& server_address, const std::string& secure) {
    RecServiceImpl rec_service;

    grpc::ServerBuilder builder;

    if(secure == "false") {
        builder.AddListeningPort(server_address, grpc::InsecureServerCredentials());
    } else {
        std::cerr << "[WARN] Unsupported secure: " << secure << " (falling back to false)\n";
        builder.AddListeningPort(server_address, grpc::InsecureServerCredentials());
    }

    builder.RegisterService(&rec_service);

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
