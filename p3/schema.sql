drop table if exists ORDERS;
drop table if exists PLAYS_AT;
drop table if exists PREFERS;
drop table if exists PAYMENT_INFO;
drop table if exists THEATER;
drop table if exists MOVIE;
drop table if exists REVIEW;
drop table if exists USER;
drop table if exists SYSTEM_INFO;


create table SYSTEM_INFO (
  cancellation_fee int primary key,
  child_discount int,
  senior_discount int,
  manager_password varchar[25]
);

create table USER (
  username varchar[30] not null primary key,
  password varchar[30] not null,
  email varchar[50] not null
);

create table REVIEW (
  title varchar[30] not null,
  review_ID int not null primary key,
  comment text,
  rating int,
  username varchar[30] not null,
  movie_title varchar[100] not null,
  constraint REVIEWUSER foreign key(username) references USER(username) on delete set null on update cascade,
  constraint MOVIETITLE foreign key(movie_title) references MOVIE(title) on delete cascade on update cascade
);

create table MOVIE (
  title varchar[100] not null primary key,
  rating varchar[5],
  genre varchar[30] not null,
  length int not null,
  avg_rating int,
  cast varchar[256],
  synopsis text not null,
  release_date date not null
);

create table THEATER (
  name varchar[50] not null,
  theater_id integer primary key autoincrement,
  state varchar[2] not null,
  city varchar[25] not null,
  street varchar[40] not null,
  zip int not null
);

create table PAYMENT_INFO (
  card_number int not null primary key,
  cvv int not null,
  saved boolean not null,
  name_on_card varchar[40] not null,
  expiration_date varchar[5] not null,
  username varchar[30] not null,
  constraint PAYMENTUSER foreign key(username) references USER(username) on delete cascade on update cascade
);

create table PREFERS (
  username varchar[30] not null primary key,
  theater_id int not null,
  constraint PREFERSUSER foreign key(username) references USER(username) on delete cascade on update cascade,
  constraint PREFERSTHEATER foreign key(theater_id) references THEATER(theater_id) on delete cascade on update cascade
);

create table PLAYS_AT (
  mtitle varchar[100] not null primary key,
  showtime time not null,
  playing boolean not null,
  tID int not null,
  constraint PLAYSTITLE foreign key(mtitle) references MOVIE(title) on delete cascade on update cascade,
  constraint PLAYSTHEATRE foreign key(tID) references THEATER(theater_id) on delete cascade on update cascade
);

create table ORDERS (
  theater_id int not null,
  card_number int not null,
  title varchar[100] not null,
  username varchar[30] not null,
  total_tickets int not null,
  adult_tickets int not null,
  child_tickets int not null,
  senior_tickets int not null,
  o_time time not null,
  o_date date not null,
  status varchar[25],
  order_ID integer not null primary key autoincrement,
  total_cost int not null,
  constraint ORDERTHEATRE foreign key(theater_id) references THEATER(theater_id) on delete set null on update cascade,
  constraint ORDERCARD foreign key(card_number) references PAYMENT_INFO(card_number) on delete set null on update cascade,
  constraint ORDERTITLE foreign key(title) references MOVIE(title) on delete set null on update cascade,
  constraint ORDERUSER foreign key(username) references USER(username) on delete set null on update cascade
);
