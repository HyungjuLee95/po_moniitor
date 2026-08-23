from __future__ import annotations


# The live SQL contract used by RtimsRepository. Keep this list synchronized
# with both DDL files and the RTIMS schema validation endpoint.
REQUIRED_OBJECTS: tuple[str, ...] = (
    "MON_MSG_LOG",
    "MON_INTF_MAP",
    "MON_DAILY_STATISTICS",
    "MON_DAILY_CLOSE_STAT",
    "MON_CHANNINFO",
    "MON_RES_USAGE",
    "MON_RESOURCE",
    "MON_AE_QUEUE",
    "MON_Q_STATUS",
    "MON_ERR_HIST",
    "PM_INTERFACE",
    "PM_INTF_GROUP",
    "SYS_ERR_CODE",
    "SYS_ERR_CATE",
)


REQUIRED_COLUMNS: dict[str, frozenset[str]] = {
    "MON_MSG_LOG": frozenset(
        {
            "LOG_ID",
            "MSG_ID",
            "MSG_STATUS",
            "INTF_MAP_ID",
            "CLIENT_ID",
            "REQ_MSG_SIZE",
            "RES_MSG_SIZE",
            "REQ_START_DTM",
            "REQ_ELAPSED_SEC",
            "PROV_ELAPSED_SEC",
            "RES_ELAPSED_SEC",
            "SERVER_ID",
            "RES_MSG_ID",
        }
    ),
    "MON_INTF_MAP": frozenset(
        {
            "INTF_MAP_ID",
            "OB_NS",
            "OB_INTF_NM",
            "OB_SYSTEM",
            "IB_NS",
            "IB_INTF_NM",
            "IB_SYSTEM",
            "SERVER_ID",
            "INTF_ID",
        }
    ),
    "MON_DAILY_STATISTICS": frozenset(
        {"INTF_MAP_ID", "YMDD", "HOUR", "MSG_STATUS", "COUNT", "LATENCY", "MAX_LATENCY"}
    ),
    "MON_DAILY_CLOSE_STAT": frozenset({"INTF_MAP_ID", "YMDD", "HOUR", "COUNT"}),
    "MON_CHANNINFO": frozenset(
        {
            "SERVER_ID",
            "CHANN_ID",
            "CHANN_NM",
            "BUSINESS_SERVICE",
            "STATE",
            "CHANN_TYPE",
            "DIRECTION",
            "ACTIVATION_STATE",
        }
    ),
    "MON_RES_USAGE": frozenset(
        {
            "SERVER_ID",
            "RESOURCE_ID",
            "NODE",
            "YMDD",
            "MINUTE_DAY",
            "RECENT_USAGE",
            "MAX_LIMIT",
        }
    ),
    "MON_RESOURCE": frozenset({"RESOURCE_ID", "TYPE", "RESOURCENM"}),
    "MON_AE_QUEUE": frozenset(
        {
            "SERVER_ID",
            "SERVERNODE",
            "QUEUENAME",
            "CONNAME",
            "STARTED",
            "NUM_ENTRIES",
            "THREADS_ASSIGNED",
            "THREADS_WORKING",
            "MAX_THREAD",
        }
    ),
    "MON_Q_STATUS": frozenset(
        {"SERVER_ID", "CLIENT_ID", "DIRECTION", "MSG_COUNT", "SEVERITY"}
    ),
    "MON_ERR_HIST": frozenset(
        {
            "ERR_LOG_ID",
            "REF_MSG_ID",
            "REF_SERVER_ID",
            "REF_CLIENT_ID",
            "REF_INTF_MAP_ID",
            "ERR_MSG",
            "ERROR_LEVEL",
            "ERR_DTM",
            "ERR_STATE",
            "ERR_PROC_MSG",
            "ERR_CODE_ID",
            "USER_ID",
        }
    ),
    "PM_INTERFACE": frozenset({"INTF_ID", "INTF_NM", "GROUP_ID", "MNG_INTF_ID"}),
    "PM_INTF_GROUP": frozenset({"GROUP_ID", "GROUP_NM"}),
    "SYS_ERR_CODE": frozenset({"ERR_CODE_ID", "ERR_CODE", "ERR_CATE_ID"}),
    "SYS_ERR_CATE": frozenset({"ERR_CATE_ID", "ERR_CATE_NM"}),
}
