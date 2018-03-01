drop table if exists users;
drop table if exists records;
create table users (
  id integer primary key autoincrement,
  name string not null,
  password string not null
);
create table records (
  id integer primary key autoincrement,
  name string not null,
  password string not null
);