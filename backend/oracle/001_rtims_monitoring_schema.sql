-- Oracle RTIMS compatibility DDL for the 14 objects used by PO_MONITOR_MAIN.
-- Execute through scripts/setup_rtims_databases.py so ORA-00955 (already
-- exists) is handled safely. No DROP, TRUNCATE, DELETE, or data mutation exists.
-- Each executable unit is separated by the marker below.

-- statement
create table PM_INTF_GROUP (
    GROUP_ID number(10) not null,
    GROUP_NM varchar2(60 byte) not null,
    USE_YN char(1 byte) not null,
    CREATE_DTM date default sysdate,
    MODIFIED_DTM date default sysdate,
    DESCRIPTION varchar2(300 byte),
    STYLE_ID number(10),
    MODIFY_USER varchar2(20 byte),
    constraint PK_PM_INTF_GROUP primary key (GROUP_ID)
)

-- statement
create table PM_INTERFACE (
    INTF_ID number(10) not null,
    INTF_NM varchar2(300 byte) not null,
    STATUS char(1 byte) not null,
    CREATE_DTM date default sysdate,
    MODIFIED_DTM date default sysdate,
    INTF_LEVEL char(1 byte) default '1' not null,
    OB_BASE_MAPPING char(1 byte) default 'N',
    PAYLOAD_YN char(1 byte) default 'N',
    ITGC_YN char(1 byte) default 'N',
    CLOUD_INTF_TYPE varchar2(20 byte) default 'NONE',
    RESPONSE_TIME number(10),
    DESCRIPTION varchar2(1000 byte),
    GROUP_ID number(10),
    MODIFY_USER varchar2(20 byte),
    MNG_INTF_ID varchar2(30 byte),
    constraint PK_PM_INTERFACE primary key (INTF_ID)
)

-- statement
create index PM_INTERFACE_IDX on PM_INTERFACE (GROUP_ID, INTF_ID)

-- statement
create table MON_INTF_MAP (
    INTF_MAP_ID number(10) not null,
    OB_NS varchar2(255 byte) not null,
    OB_INTF_NM varchar2(100 byte) not null,
    OB_SYSTEM varchar2(60 byte) not null,
    IB_NS varchar2(255 byte) not null,
    IB_INTF_NM varchar2(100 byte) not null,
    IB_SYSTEM varchar2(60 byte) not null,
    SERVER_ID varchar2(10 byte) not null,
    FIRST_TS timestamp(6),
    LAST_TS timestamp(6),
    PATTERN_ID number(10) not null,
    INTF_ID number(10) not null,
    constraint PK_MON_INTF_MAP primary key (INTF_MAP_ID),
    constraint UQ_MON_INTF_MAP_ROUTE unique (
        OB_NS, OB_INTF_NM, OB_SYSTEM, IB_NS, IB_INTF_NM, IB_SYSTEM, SERVER_ID
    )
)

-- statement
create index MON_INTF_MAP_IDX1 on MON_INTF_MAP (INTF_ID)

-- statement
create table MON_MSG_LOG (
    LOG_ID number(20) not null,
    MSG_ID varchar2(64 byte),
    MSG_STATUS varchar2(3 byte),
    INTF_MAP_ID number(10),
    TYPE char(1 byte),
    CLIENT_ID varchar2(3 byte),
    REQ_MSG_SIZE integer,
    RES_MSG_SIZE integer,
    REQ_START_DTM timestamp(6),
    REQ_END_DTM timestamp(6),
    RES_START_DTM timestamp(6),
    RES_END_DTM timestamp(6),
    REQ_ELAPSED_SEC number(15,3),
    PROV_ELAPSED_SEC number(15,3),
    RES_ELAPSED_SEC number(15,3),
    SERVER_ID varchar2(10 byte),
    CLOSED char(1 byte) default 'N' not null,
    HOST_ID varchar2(80 byte),
    RES_MSG_ID varchar2(64 byte),
    PERSIST_UNTIL_TS timestamp,
    constraint PK_MON_MSG_LOG primary key (LOG_ID)
)

-- statement
create index MON_MSG_LOG_IDX1 on MON_MSG_LOG (MSG_ID)

-- statement
create index MON_MSG_LOG_IDX2 on MON_MSG_LOG (RES_MSG_ID)

-- statement
create index MON_MSG_LOG_IDX3 on MON_MSG_LOG (REQ_START_DTM)

-- statement
create index MON_MSG_LOG_IDX4 on MON_MSG_LOG (REQ_START_DTM, INTF_MAP_ID)

-- statement
create index MON_MSG_LOG_PER_INDEX1 on MON_MSG_LOG (PERSIST_UNTIL_TS)

-- statement
create table MON_DAILY_STATISTICS (
    INTF_MAP_ID number(10) not null,
    YMDD varchar2(8 byte) not null,
    HOUR number(2) not null,
    MSG_STATUS varchar2(3 byte) not null,
    COUNT number(10) default 0,
    VOLUME number(20) default 0,
    LATENCY number(15,3) default 0,
    MAX_LATENCY number(15,3) default 0,
    constraint PK_MON_DAILY_STATISTICS primary key (
        INTF_MAP_ID, YMDD, HOUR, MSG_STATUS
    ),
    constraint CK_MON_DAILY_STAT_HOUR check (HOUR between 0 and 23)
)

-- statement
-- Provisional minimum contract. The supplied legacy material did not contain
-- the original DDL; these are the columns used by system_statistics().
create table MON_DAILY_CLOSE_STAT (
    INTF_MAP_ID number(10) not null,
    YMDD varchar2(8 byte) not null,
    HOUR number(2) not null,
    COUNT number(10) default 0,
    constraint PK_MON_DAILY_CLOSE_STAT primary key (INTF_MAP_ID, YMDD, HOUR),
    constraint CK_MON_DAILY_CLOSE_HOUR check (HOUR between 0 and 23)
)

-- statement
create table MON_CHANNINFO (
    SERVER_ID varchar2(10 byte) not null,
    CHANN_ID varchar2(32 byte) not null,
    CHANN_NM varchar2(60 byte) not null,
    BUSINESS_SERVICE varchar2(60 byte),
    STATE char(10 byte),
    CHANN_TYPE varchar2(20 byte),
    LAST_MDFY_DTM date,
    DIRECTION char(1 byte) not null,
    AUTOMATION varchar2(20 byte),
    ACTIVATION_STATE varchar2(20 byte),
    CONNECTION_URL varchar2(4000 byte),
    DB_USER varchar2(100 byte),
    PERIOD varchar2(50 byte),
    DESTINATION varchar2(200 byte),
    QOS varchar2(50 byte),
    LAST_ERR_SINCE number(20),
    SHORT_TXT varchar2(800 byte),
    LAST_PROC_MSGS varchar2(2000 byte),
    SELECT_QUERY clob,
    PERSIST_UNTIL_TS timestamp,
    constraint PK_MON_CHANNINFO primary key (SERVER_ID, CHANN_ID)
)

-- statement
create table MON_RESOURCE (
    RESOURCE_ID number(10) not null,
    TYPE varchar2(10 byte),
    RESOURCENM varchar2(100 byte),
    DESCRIPTION varchar2(100 byte),
    constraint PK_MON_RESOURCE primary key (RESOURCE_ID)
)

-- statement
create table MON_RES_USAGE (
    SERVER_ID varchar2(10 byte) not null,
    RESOURCE_ID number(10) not null,
    NODE varchar2(24 byte) not null,
    YMDD varchar2(8 byte) not null,
    MINUTE_DAY number(5) not null,
    SUM_USAGE number(15,3) default 0,
    MAX_USAGE number(15,3) default 0,
    MIN_USAGE number(15,3) default 0,
    RECENT_USAGE number(15,3) default 0,
    MAX_LIMIT number(15,3) default 0,
    USAGE_CNT number(5) default 0,
    PERSIST_UNTIL_TS timestamp,
    constraint PK_MON_RES_USAGE primary key (
        SERVER_ID, RESOURCE_ID, NODE, YMDD, MINUTE_DAY
    ),
    constraint CK_MON_RES_MINUTE_DAY check (MINUTE_DAY between 0 and 1439)
)

-- statement
create table MON_AE_QUEUE (
    SERVER_ID varchar2(10 byte) not null,
    SERVERNODE varchar2(20 byte) not null,
    QUEUENAME varchar2(50 byte) not null,
    CONNAME varchar2(50 byte) not null,
    STARTED varchar2(1 byte) not null,
    NUM_ENTRIES number(10),
    THREADS_ASSIGNED number(5),
    THREADS_WORKING number(5),
    MAX_THREAD number(5),
    PERSIST_UNTIL_TS timestamp,
    constraint PK_MON_AE_QUEUE primary key (
        SERVER_ID, SERVERNODE, QUEUENAME, CONNAME
    )
)

-- statement
create table MON_Q_STATUS (
    SERVER_ID varchar2(24 byte) not null,
    CLIENT_ID varchar2(3 byte) not null,
    DIRECTION char(1 byte) not null,
    MSG_COUNT integer,
    SEVERITY char(1 byte) not null,
    CREATE_DTM varchar2(14 byte),
    PERSIST_UNTIL_TS timestamp,
    constraint PK_MON_Q_STATUS primary key (
        SERVER_ID, CLIENT_ID, DIRECTION, SEVERITY
    )
)

-- statement
create table SYS_ERR_CATE (
    ERR_CATE_ID number(10) not null,
    ERR_CATE_NM varchar2(50 byte) not null,
    ERR_CATE_DESC varchar2(200 byte),
    constraint PK_SYS_ERR_CATE primary key (ERR_CATE_ID)
)

-- statement
create table SYS_ERR_CODE (
    ERR_CODE_ID number(10) not null,
    ERR_CODE varchar2(45 byte),
    ERR_LEVEL char(1 byte),
    ERR_DESC varchar2(200 byte),
    ERR_CATE_ID number(10) not null,
    constraint PK_SYS_ERR_CODE primary key (ERR_CODE_ID)
)

-- statement
create table MON_ERR_HIST (
    ERR_LOG_ID number(20) not null,
    REF_MSG_ID varchar2(32 byte),
    REF_SERVER_ID varchar2(20 byte),
    REF_CLIENT_ID varchar2(3 byte),
    REF_INTF_MAP_ID number(10),
    ERR_MSG varchar2(1536 byte),
    ERROR_LEVEL char(1 byte),
    ERR_DTM timestamp,
    ERR_STATE char(1 byte) default 'O',
    ERR_PROC_MSG varchar2(4000 byte),
    ERR_CODE_ID number(10),
    USER_ID varchar2(24 byte),
    PERSIST_UNTIL_TS timestamp,
    constraint PK_MON_ERR_HIST primary key (ERR_LOG_ID)
)

-- statement
create index MON_ERR_HIST_IDX1 on MON_ERR_HIST (REF_MSG_ID)

-- Supporting sequences named by the supplied legacy schema analysis. Their
-- cache/start settings were not documented, so conservative defaults are used.
-- statement
create sequence PM_INTF_GROUP_ID start with 1 increment by 1 nocache

-- statement
create sequence PM_INTF_ID start with 1 increment by 1 nocache

-- statement
create sequence MON_INTF_MAP_ID start with 1 increment by 1 nocache

-- statement
create sequence MON_MSG_LOG_ID start with 1 increment by 1 nocache

-- statement
create sequence MON_RESOURCE_ID start with 1 increment by 1 nocache

-- statement
create sequence MON_ERR_LOG_ID start with 1 increment by 1 nocache

-- statement
create sequence SYS_ERR_CODE_ID start with 1 increment by 1 nocache

-- statement
create sequence SYS_ERR_CATE_ID start with 1 increment by 1 nocache
