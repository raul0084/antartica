import pandas as pd
from datetime import datetime
from sqlalchemy import text

# USED IF CALLING CALLS FROM DB AND NOT DF
def get_port_calls(
    engine,
    date_start=None,
    date_end=None,
    eslora_from=None,
    eslora_to=None,
    vessel_type=None,
    imo=None
):
    """
    Returns a DataFrame of port calls filtered by the given parameters.
    All filters are optional and default to no filtering.

    Args:
        engine:          SQLAlchemy engine connected to the database.
        date_start (datetime):   Filter calls from this date onwards.
        date_end (datetime):     Filter calls up to and including this date.
        eslora_from (str):  Filter calls departing from this port code.
        eslora_to (str):    Filter calls arriving at this port code.
        vessel_type (str):  Filter by vessel type.
        imo (int):          Filter by IMO number.

    Returns:
        pd.DataFrame: Filtered port calls, sorted by etautc.
    """
    conditions = []
    params = {}

    if date_start is not None and date_end is not None:
        conditions.append("etautc BETWEEN :date_start AND :date_end")
        params["date_start"] = date_start
        params["date_end"] = date_end

    if date_start is not None and date_end is None:
        conditions.append("etautc >= :date_start")
        params["date_start"] = date_start   

    if date_start is None and date_end is not None:
        conditions.append("etautc <= :date_end")
        params["date_end"] = date_end

    if eslora_from is not None:
        conditions.append("eslora_metres >= :eslora_from")
        params["eslora_from"] = eslora_from

    if eslora_to is not None:
        conditions.append("eslora_metres <= :eslora_to")
        params["eslora_to"] = eslora_to

    if vessel_type is not None:
        conditions.append("vaixelltipus = :vessel_type")
        params["vessel_type"] = vessel_type

    if imo is not None:
        conditions.append("imo = :imo")
        params["imo"] = imo

    where_clause = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    query = text(f"""
        SELECT *
        FROM port_calls
        {where_clause}
        ORDER BY etautc
    """)

    with engine.connect() as connection:
        return pd.read_sql(query, connection, params=params)

# USED IF CALLING VESSELS FROM DB AND NOT DF
def get_all_vessels(engine):
    """
    Returns a DataFrame with all vessels and their corresponding IMO, MMSI, name, fuel type and power data. 
    This can be used to enrich the port calls data with vessel information for emissions calculations.
    Args:
        engine: SQLAlchemy engine connected to the database.

    """

    query = text("""
        SELECT imo, mmsi, vaixellnom, p_main, p_aux, p_gt, fuel
        FROM vessels
    """)

    with engine.connect() as connection:
        return pd.read_sql(query, connection)
    
def get_fuel_type(
        engine, 
        imo=None, 
        mmsi=None, 
        vessel_name=None
    ):
    """
    Returns the fuel type (str) for a specific ship identified by IMO, MMSI, or vessel name. 
    If no data is found for the specified ship it returns LNG as generic fuel data.
    Args:
        engine:         SQLAlchemy engine connected to the database.
        imo (int):      IMO number of the ship (optional).
        mmsi (int):     MMSI number of the ship (optional).
        vessel_name (str): Name of the ship (optional).
        vessel_type (str): Type of the vessel for filtering fuel data (default is "generic").
    """
    conditions = []
    params = {}

    if imo:
        conditions.append("imo = :imo")
        params["imo"] = imo
    elif mmsi:
        conditions.append("mmsi = :mmsi")
        params["mmsi"] = mmsi
    elif vessel_name:
        conditions.append("vaixellnom = :vessel_name")
        params["vessel_name"] = vessel_name
    else:
        return "LNG"  # Default fuel type if no identifiers are provided

    where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

    query = text(f"""
        SELECT fuel
        FROM vessels
        {where_clause}
    """)

    with engine.connect() as connection:
        df = pd.read_sql(query, connection, params=params)

    if df.empty:
        return "LNG"  # Default fuel type if no data is found

    if df["fuel"].iloc[0] == "MDO/MGO":
        return "MDO_MGO"
    elif df["fuel"].iloc[0] == "BOTH":
        return "LNG"
    else:
        return "LNG"
    
def get_unknown_fuel_data(engine):
    """
    Returns a DataFrame with the port calls that have no fuel data available in the database. 
    This can be used to identify which ships or port calls need to be prioritized for fuel data collection.
    Args:
        engine: SQLAlchemy engine connected to the database.

    """

    query = text("""
        SELECT DISTINCT pc.vaixellnom, pc.imo, pc.mmsi
        FROM port_calls pc
        LEFT JOIN vessels v 
            ON pc.imo = v.imo 
            OR pc.mmsi = v.mmsi 
            OR pc.vaixellnom = v.vaixellnom
        WHERE v.imo IS NULL 
            AND v.mmsi IS NULL 
            AND v.vaixellnom IS NULL
        ORDER BY pc.vaixellnom;
            """)

    with engine.connect() as connection:
        return pd.read_sql(query, connection)

def get_power(
    engine,
    imo=None,
    mmsi=None, 
    vessel_name=None
):
    """
    Returns the main and auxiliary engine power (P_main, P_aux, P_gt) for a specific ship identified by IMO, MMSI, or vessel name. 
    If no data is found for the specified ship it returns default power values (P_main=10000 kW, P_aux=2000 kW, P_gt=5000 kW).
    Args:
        engine:         SQLAlchemy engine connected to the database.
        imo (int):      IMO number of the ship (optional).
        mmsi (int):     MMSI number of the ship (optional).
        vessel_name (str): Name of the ship (optional).
    """
    conditions = []
    params = {}

    if imo:
        conditions.append("imo = :imo")
        params["imo"] = imo
    elif mmsi:
        conditions.append("mmsi = :mmsi")
        params["mmsi"] = mmsi
    elif vessel_name:
        conditions.append("vaixellnom = :vessel_name")
        params["vessel_name"] = vessel_name
    else:
        return 10000, 2000, 5000  # Default power values if no identifiers are provided

    where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

    query = text(f"""
        SELECT p_main, p_aux, p_gt
        FROM vessels
        {where_clause}
    """)

    with engine.connect() as connection:
        df = pd.read_sql(query, connection, params=params)

    if not df.empty:
        return df["p_main"].iloc[0], df["p_aux"].iloc[0], df["p_gt"].iloc[0]
    else:
        return 10000, 2000, 5000  # Default power values if no data is found

