drop table if exists users;
drop table if exists topics;
drop table if exists questions;
drop table if exists records;
drop table if exists skill2topic;
create table users (
  id integer primary key autoincrement,
  name string not null,
  password string not null
);
create table skill2topic (
  skill_name string primary key not null,
  topic_id integer not null
);
create table topics (
  topic_id integer primary key autoincrement,
  topic_name string not null,
  description string
);
create table questions (
  id integer primary key autoincrement,
  description string,
  topic_id integer not null
);
create table records (
  id integer primary key autoincrement,
  user_id integer,
  log_ip string not null,
  log_time timestamp not null,
  correct integer not null,
  question_id integer not null
);