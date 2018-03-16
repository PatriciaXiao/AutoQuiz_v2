drop table if exists users;
drop table if exists records;
drop table if exists topics;
drop table if exists links;
drop table if exists questions;
drop table if exists skill2topic;
create table users (
  id integer primary key autoincrement,
  name string not null,
  password string not null,
  reg_time timestamp not null
);
create table records (
  id integer primary key autoincrement,
  user_id integer,
  log_ip string not null,
  log_time timestamp not null,
  correct integer not null,
  question_id integer not null
);
create table topics (
  topic_id integer primary key autoincrement,
  topic_name string not null,
  description string
);
create table links (
  id integer primary key autoincrement,
  source integer not null,
  target integer not null
);
create table questions (
  question_id integer primary key,
  description string,
  skill_id integer not null,
  topic_id integer not null
);
create table skill2topic (
  skill_id integer primary key autoincrement,
  skill_name string not null unique,
  topic_id integer not null
);

drop table if exists next_question_map;
create table next_question_map (
  temp_id integer primary key,
  next_id not null
);