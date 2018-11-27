drop table if exists MANAGER;
drop table if exists CUSTOMER;
drop table if exists REVIEW;
drop table if exists PAYMENT_INFO;
drop table if exists ORDERS;
drop table if exists MOVIE;
drop table if exists PLAYS_AT;
drop table if exists SHOWTIME;
drop table if exists THEATER;
drop table if exists SYSTEM_INFO;
drop table if exists PREFERS;

create table MANAGER (
  username varchar[30] not null primary key,
  email varchar[60] not null unique,
  password varchar[30] not null
);

create table CUSTOMER (
  username varchar[30] not null primary key,
  email varchar[60] not null unique,
  password varchar[30] not null
);

create table REVIEW (
  review_ID integer primary key autoincrement,
  title varchar[60] not null,
  mtitle varchar[100] not null,
  comment text,
  rating int,
  username varchar[30] not null,
  constraint REVIEWMOVIE foreign key(mtitle) references MOVIE(title) on delete cascade on update cascade
);

create table PAYMENT_INFO (
  card_no int not null primary key,
  cvv int not null,
  name_on_card varchar[50] not null,
  expiration_date varchar[7] not null,
  saved boolean not null,
  username varchar[30] not null,
  constraint PAYMENTUSER foreign key(username) references CUSTOMER(username) on delete cascade on update cascade
);

create table ORDERS (
  order_ID integer primary key autoincrement,
  o_date date not null,
  senior_tickets int not null,
  child_tickets int not null,
  adult_tickets int not null,
  total_tickets int not null,
  o_time time not null,
  status varchar[30],
  card_number int not null,
  username varchar[30] not null,
  title varchar[100] not null,
  theater_id int not null,
  constraint ORDERCARD foreign key(card_number) references PAYMENT_INFO(card_number) on delete set null on update cascade,
  constraint ORDERUSER foreign key(username) references CUSTOMER(username) on delete set null on update cascade,
  constraint ORDERTITLE foreign key(title) references MOVIE(title) on delete set null on update cascade,
  constraint ORDERTHEATER foreign key(theater_id) references THEATER(theater_id) on delete set null on update cascade
);

create table MOVIE (
  title varchar[100] not null primary key,
  synopsis text not null,
  length int not null,
  genre varchar[40] not null,
  release_date date not null,
  rating varchar[5]
);

create table CAST (
  ID integer not null primary key autoincrement,
  mtitle varchar[100] not null,
  actor varchar[200] not null,
  role varchar[200] not null,
  constraint CASTMOVIE foreign key(mtitle) references MOVIE(title) on delete cascade on update cascade
);

create table PLAYS_AT (
  ID integer not null primary key autoincrement,
  playing BIT not null,
  mtitle varchar[100] not null,
  tID int not null,
  constraint PLAYSTITLE foreign key(mtitle) references MOVIE(title) on delete cascade on update cascade,
  constraint PLAYSTHEATRE foreign key(tID) references THEATER(theater_id) on delete cascade on update cascade
);

create table SHOWTIME (
  ID integer not null primary key autoincrement,
  showtime time not null,
  mtitle varchar[100] not null,
  tID int not null,
  am BIT not null,
  constraint SHOWTITLE foreign key(mtitle) references MOVIE(title) on delete cascade on update cascade,
  constraint SHOWTHEATRE foreign key(tID) references THEATER(theater_id) on delete cascade on update cascade
);

create table THEATER (
  theater_id integer primary key autoincrement,
  name varchar[60] not null,
  state varchar[2] not null,
  city varchar[25] not null,
  street varchar[40] not null,
  zip int not null
);

create table SYSTEM_INFO (
  cancellation_fee int primary key,
  manager_password varchar[30],
  child_discount int,
  senior_discount int
);

create table PREFERS (
  ID integer not null primary key autoincrement,
  theater_id int not null,
  username varchar[30] not null,
  constraint PREFERSUSER foreign key(username) references CUSTOMER(username) on delete cascade on update cascade,
  constraint PREFERSTHEATER foreign key(theater_id) references THEATER(theater_id) on delete cascade on update cascade
);
