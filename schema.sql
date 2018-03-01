drop table if exists users;
drop table if exists skills;
drop table if exists questions;
drop table if exists records;
create table users (
  id integer primary key autoincrement,
  name string not null,
  password string not null
);
create table skills (
  id integer primary key autoincrement,
  name string not null,
  description string
);
create table questions (
  id integer primary key autoincrement,
  description string not null,
  skill integer not null
);
create table records (
  id integer primary key autoincrement,
  user_id integer not null,
  log_ip string not null
);