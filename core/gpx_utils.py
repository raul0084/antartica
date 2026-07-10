"""
gpx_utils.py

Helpers for the route-based simulation input:
    - parse an uploaded GPX file into a DataFrame of waypoints
    - compute great-circle route distance (nautical miles)
    - turn distance + cruising speed into navigation time (hours)
    - build a GPX file (bytes) from manually entered waypoints, for download

Requires: gpxpy  (pip install gpxpy)
"""

import numpy as np
import pandas as pd
import gpxpy
import gpxpy.gpx

EARTH_RADIUS_KM = 6371.0088
NM_PER_KM = 1 / 1.852


def parse_gpx(file) -> pd.DataFrame:
    """
    Parses a GPX file (file-like object, e.g. from st.file_uploader) into
    a DataFrame with columns: lat, lon, ele, time.

    Reads track points first (most common for real routes/AIS exports),
    falls back to route points, then waypoints.
    """
    gpx = gpxpy.parse(file)

    points = []

    for track in gpx.tracks:
        for segment in track.segments:
            for p in segment.points:
                points.append({"lat": p.latitude, "lon": p.longitude,
                                "ele": p.elevation, "time": p.time})

    if not points:
        for route in gpx.routes:
            for p in route.points:
                points.append({"lat": p.latitude, "lon": p.longitude,
                                "ele": p.elevation, "time": p.time})

    if not points:
        for wp in gpx.waypoints:
            points.append({"lat": wp.latitude, "lon": wp.longitude,
                            "ele": wp.elevation, "time": wp.time})

    if not points:
        raise ValueError("No track, route, or waypoint data found in this GPX file.")

    return pd.DataFrame(points)


def _haversine_nm(lat1, lon1, lat2, lon2):
    """Vectorized great-circle distance between paired points, in nautical miles."""
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    c = 2 * np.arcsin(np.sqrt(a))
    return EARTH_RADIUS_KM * c * NM_PER_KM


def route_distance_nm(points_df: pd.DataFrame) -> float:
    """
    Total route distance (sum of leg-by-leg great-circle distances),
    in nautical miles. Requires columns 'lat' and 'lon', in order.
    """
    if len(points_df) < 2:
        return 0.0

    lat1 = points_df["lat"].to_numpy()[:-1]
    lon1 = points_df["lon"].to_numpy()[:-1]
    lat2 = points_df["lat"].to_numpy()[1:]
    lon2 = points_df["lon"].to_numpy()[1:]

    return float(_haversine_nm(lat1, lon1, lat2, lon2).sum())


def estimate_nav_time(distance_nm: float, speed_kn: float) -> float:
    """Navigation time in hours, given distance (nm) and cruising speed (knots)."""
    if speed_kn is None or speed_kn <= 0:
        raise ValueError("Cruising speed must be greater than 0 knots.")
    return distance_nm / speed_kn


def build_gpx(points_df: pd.DataFrame, name: str = "voyage") -> bytes:
    """
    Builds a GPX file (as UTF-8 bytes, ready for st.download_button) from
    a DataFrame of waypoints. Requires 'lat' and 'lon'; 'ele' and 'time'
    are used if present.
    """
    gpx = gpxpy.gpx.GPX()
    track = gpxpy.gpx.GPXTrack(name=name)
    gpx.tracks.append(track)
    segment = gpxpy.gpx.GPXTrackSegment()
    track.segments.append(segment)

    for _, row in points_df.iterrows():
        segment.points.append(
            gpxpy.gpx.GPXTrackPoint(
                latitude=row["lat"],
                longitude=row["lon"],
                elevation=row["ele"] if "ele" in row and pd.notna(row["ele"]) else None,
                time=row["time"] if "time" in row and pd.notna(row["time"]) else None,
            )
        )

    return gpx.to_xml().encode("utf-8")