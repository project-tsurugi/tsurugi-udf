drop table if exists t_date_return;
drop table if exists t_decimal_return;
drop table if exists t_time_return;
drop table if exists t_timestamp_return;
drop table if exists t_timestamptz_return;
drop table if exists t_blob_return;
drop table if exists t_clob_return;

-- tablemake
create table t_date_return(v DATE);
create table t_decimal_return (v decimal(15, 2));
create table t_time_return(v TIME);
create table t_timestamp_return(v TIMESTAMP);
create table t_timestamptz_return(v TIMESTAMP WITH TIME ZONE);
create table t_blob_return(v BLOB);
create table t_clob_return(v CLOB);
-- insert
insert into t_date_return VALUES(date'2000-01-01');
insert into t_decimal_return values (1234.53);
insert into t_time_return VALUES(time'12:34:56');
insert into t_timestamp_return VALUES(timestamp'2001-01-01 11:22:33');
insert into t_timestamptz_return VALUES(timestamp with time zone '2001-01-01 11:22:33+09');
insert into t_blob_return VALUES(X'1234');
insert into t_clob_return VALUES('abc');
-- tablemake
select inc_date(v) from t_date_return;
select inc_decimal(v) from t_decimal_return;
select inc_local_time(v) from t_time_return;
select inc_local_date_time(v) from t_timestamp_return;
select inc_offset_date_time(v) from t_timestamptz_return;
select inc_blob_referece(v) from t_blob_return;
select inc_clob_referece(v) from t_clob_return;
