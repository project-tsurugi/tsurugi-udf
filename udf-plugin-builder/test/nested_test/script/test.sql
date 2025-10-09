drop table if exists t_varchar;
drop table if exists t_decimal;
drop table if exists t_decimal2;
-- tablemake
create table t_varchar (v varchar(30));
create table t_decimal (v decimal(15, 2));
create table t_decimal2 (v1 int ,v2 decimal(15, 1));
-- insert
insert into t_varchar values ('hello world');
insert into t_decimal values (1234.53);
insert into t_decimal2 values (5,98765.4);
-- tablemake
select NestedHello(v) from t_varchar;
select DecimalOne(v) from t_decimal;
select DecimalTwo(v1,v2) t_decimal2;
