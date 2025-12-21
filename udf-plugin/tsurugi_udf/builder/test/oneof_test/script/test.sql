drop table if exists t_int32;
drop table if exists t_bigint;
drop table if exists t_string;
drop table if exists a1;
drop table if exists a2;
drop table if exists a3;
drop table if exists a4;
-- tablemake
create table t_int32 (v int);
create table t_bigint (v bigint);
create table t_string (v varchar(30));
create table a1 (v1 bigint,v2 bigint,v3 int,v4 bigint);
create table a2 (v1 bigint,v2 varchar(30),v3 int,v4 bigint);
create table a3 (v1 bigint,v2 bigint,v3 int,v4 varchar(30));
create table a4 (v1 bigint,v2 varchar(30),v3 int,v4 varchar(30));
-- insert
insert into t_int32 values (123);
insert into t_bigint values (456);
insert into t_string values ('hello world');
insert into a1 values (1,2,3,4);
insert into a2 values (5,'hello',6,7);
insert into a3 values (8,9,10,'world');
insert into a4 values (11,'foo',12,'bar');
-- tablemake

select OneofAlpha(v) from t_int32;
select OneofBeta(v) from t_bigint;
select OneofBeta(v) from t_string;
select echooneof(v1,v2,v3,v4) from a1;
select echooneof(v1,v2,v3,v4) from a2;
select echooneof(v1,v2,v3,v4) from a3;
select echooneof(v1,v2,v3,v4) from a4;
