drop table if exists t_int32_pac;
drop table if exists t_char_pac;
-- tablemake
create table t_int32_pac (v int);
create table t_char_pac (v char(30));
-- insert
insert into t_int32_pac values (123);
insert into t_char_pac values ('hello world');
-- check
select pacsayhello(v) from t_char_pac;
select pacintaddint(v) from t_int32_pac;
select pacsayworld(v) from t_char_pac;
