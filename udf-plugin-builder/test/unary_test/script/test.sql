drop table if exists t_int32;
drop table if exists t_bigint;
drop table if exists t_real;
drop table if exists t_float;
drop table if exists t_double;

-- tablemake
create table t_int32 (v int);
create table t_bigint (v bigint);
create table t_real (v real);
create table t_float (v float);
create table t_double (v double);

-- insert
insert into t_int32 values (123);
insert into t_bigint values (1234567890123);
insert into t_real values (3.14);
insert into t_float values (1.23);
insert into t_double values (1.0e100);

-- check
select EchoInt32(v) from t_int32;
select EchoUInt32(v) from t_int32;
select EchoSInt32(v) from t_int32;
select EchoFixed32(v) from t_int32;
select EchoSFixed32(v) from t_int32;
select EchoInt64(v) from t_bigint;
select EchoUInt64(v) from t_bigint;
select EchoSInt64(v) from t_bigint;
select EchoFixed64(v) from t_bigint;
select EchoSFixed64(v) from t_bigint;
select EchoFloat(v) from t_float;
select EchoFloat(v) from t_float;
select EchoFloat(v) from t_real;
select EchoDouble(v) from t_double;
