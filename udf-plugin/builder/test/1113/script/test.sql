drop table if exists t_bigint_add;
-- tablemake
create table t_bigint_add(v1 bigint,v2 bigint);
-- insert
insert into t_bigint_add values (111,222);
-- tablemake
select noname(v1,v2) from t_bigint_add;
