show databases;
create database toll_base;
use toll_base;
create table users(username varchar(20),password varchar(64),carid int,money int,user_prividelige char(1));
# d->driver | t->toll_admin | b->blacklisted
create table cars(carid int AUTO_INCREMENT primary key,license_no varchar(15),make varchar(20),model varchar(20));
create table tokens(tokenid int AUTO_INCREMENT primary key,tokena blob,tokenb blob);
create table token_dist(tollid int,carid int,tokenid int,schedule timestamp);
create table transit(transid int AUTO_INCREMENT primary key,carid int,time_local timestamp,time_server timestamp,tollid int,laneid int);
create table tolls(tollid int AUTO_INCREMENT primary key,locn varchar(20),loce varchar(20),no_of_lanes int);

insert into cars values(NULL,'IN AA 9234','aston martin','vulcan');
insert into users values('u1','bb82030dbc2bcaba32a90bf2e207a84a856fc5f033b77c480836ab6f77f40f19',1,200,'d');#pass u1
insert into tolls values(NULL,'17.457067','78.665835',3);
insert into tokens values(null,'a03be93a77c247fc730de49998da4ecaad83150627cc8730b1c84a3df54bebf6','a03be93a77c247fc730de49998da4ecaad83150627cc8730b1c84a3df54bebf6');
insert into token_dist values(1,1,21,'2020-05-14 17:54:24');

select * from cars;
select * from users;
select * from tolls;
select * from token_dist where tollid=1 and carid in (select carid from users where username='u1');
select carid,license_no,make,model from cars where carid in (select carid from transit where tollid=1);
select * from token_dist;
select * from tokens;
select count(*) from users;
select count(*) from tokens;
select tokena,tokenb from tokens where tokenid in (select tokenid from token_dist where carid in (select carid from users where username='u1'));
select token_dist.carid,tokens.tokena,tokens.tokenb from tokens,token_dist where tokens.tokenid=token_dist.tokenid and token_dist.tollid='1';

update users set user_prividelige='b' where username='u1' and user_prividelige='d';

delete from token_dist where tollid=21;
delete from tokens where tokenid=20;

#drop table token_dist;