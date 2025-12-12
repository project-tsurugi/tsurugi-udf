drop table if exists t_int32;
drop table if exists t_char;
-- tablemake
create table t_int32 (v int);
create table t_char (v char(30));
-- insert
insert into t_int32 values (123);
insert into t_char values ('hello world');
-- check
select sayhello(v) from t_char;
select intaddint(v) from t_int32;
select sayworld(v) from t_char;
select emptyreq() from t_int32;
