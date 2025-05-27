"""=====================================================================================================================
Name: read_and_query_geoparquet.py
Purpose: Provides a hands-on example for the blog, "How to Read and Query GeoParquet in ArcGIS Pro with DuckDB".

Requirements:
    - DuckDB v1.1 which comes with ArcGIS Pro 3.5+ by default.

Author: Ed Conrad
Created: 5/27/2025
====================================================================================================================="""

import arcpy
import os
import duckdb
from collections import namedtuple


def main():
    profile = os.environ['USERPROFILE']
    pro_project = os.path.join(profile, r'Documents\ArcGIS\Projects\Data_Management\Data_Management.aprx')
    aprx = arcpy.mp.ArcGISProject(pro_project)
    gdb = aprx.defaultGeodatabase
    arcpy.env.workspace = gdb
    feature_datasets = arcpy.ListDatasets()
    wgs84 = arcpy.SpatialReference(4326)
    fd_name = 'Colorado'
    if fd_name not in feature_datasets:
        print(f"Creating a feature dataset called 'Colorado' in {gdb}")
        arcpy.management.CreateFeatureDataset(gdb, out_name=fd_name, spatial_reference=wgs84)

    out_path = os.path.join(gdb, fd_name)
    arcpy.env.overwriteOutput = True

    # Create a DuckDB Database instance
    conn = duckdb.connect()
    conn.sql('install spatial;load spatial;')  # Geospatial extension that adds support for working with spatial data and functions
    conn.sql('install httpfs;load httpfs;')    # Adds support for reading and writing files over an HTTP(S) or S3 connection
    conn.sql("set s3_region='us-west-2';")     # Tells DuckDB which AWS region to use when connecting to S3 buckets
    conn.sql('set enable_object_cache=true;')  # Improves performance by caching S3 reads locally for reuse

    # Define a BoundingBox named tuple and populate it with Colorado's bounding box values
    BoundingBox = namedtuple(typename='BoundingBox', field_names=['xmin', 'xmax', 'ymin', 'ymax'])
    colorado_bbox = BoundingBox(xmin=-109, xmax=-102, ymin=37, ymax=41)
    colorado_bbox = BoundingBox(xmin=-108.2, xmax=-104.5, ymin=37, ymax=41)

    # Query Colorado mountain peaks from the Overture Maps dataset using DuckDB.
    # Overture Maps is an open data initiative that provides geospatial data in GeoParquet format,
    # which can be queried efficiently using DuckDB’s built-in Parquet and spatial extensions.
    # Dataset Schema: https://docs.overturemaps.org/schema/reference/base/land/
    # Note 1: GeoParquet stores geometries in a Well-Known Binary (WKB), which means it supports all vector
    #         geometry types defined by the OGC Simple Features standard.
    # Note 2: we leverage DuckDB's SQL dialect to select only the columns we want, passing a boundary box to limit the
    #         results to Colorado, and we make use of DuckDB's read_parquet() method and the DuckDB spatial extension's
    #         ST_AsWKB method to read the WKB
    # Overture Maps regularly updates the data;
    # NOTE: GeoParquet is an immutable file type, meaning new GeoParquet files are created if there's a change
    release = '2025-05-21.0'
    sql = f"""
        SELECT
            names.primary AS name,
            CAST(elevation AS INT) AS elevation_meters,
            CAST(elevation * 3.28084 AS INT) AS elevation_ft,
            elevation * 3.28084 > 14000 AS Is_Fourteener,
            ST_AsWKB(geometry) AS wkb
        FROM
            read_parquet(
                's3://overturemaps-us-west-2/release/{release}/theme=base/type=land/*',
                filename=true, 
                hive_partitioning=1
            )
        WHERE 
            subtype = 'physical' AND class IN ('peak','volcano') AND elevation IS NOT NULL
            AND elevation * 3.28084 > 14000
            AND bbox.xmin BETWEEN {colorado_bbox.xmin} AND {colorado_bbox.xmax}
            AND bbox.ymin BETWEEN {colorado_bbox.ymin} AND {colorado_bbox.ymax}
    """

    # Get DuckDB Query Relation object
    duck_peaks = conn.sql(sql)

    # Insert that data read from GeoParquet into an Esri Feature Class
    import arcpy
    print('Creating the Colorado_Fourteeners feature class...')
    peaks_fc = arcpy.management.CreateFeatureclass(out_path=out_path,
                                                   out_name='Colorado_Fourteeners',
                                                   geometry_type='POINT',
                                                   spatial_reference=wgs84).getOutput(0)
    arcpy.management.AddField(in_table=peaks_fc, field_name='Name', field_type='TEXT', field_length=50)
    arcpy.management.AddField(in_table=peaks_fc, field_name='Elevation_meters', field_type='SHORT')
    arcpy.management.AddField(in_table=peaks_fc, field_name='Elevation_ft', field_type='SHORT')
    arcpy.management.AddField(in_table=peaks_fc, field_name='Is_Fourteener', field_type='SHORT')
    with arcpy.da.InsertCursor(peaks_fc, field_names=['Name', 'Elevation_meters', 'Elevation_ft', 'Is_Fourteener',
                                                      'shape@']) as iCursor:
        # Fetches a single row as a tuple
        raw_row = duck_peaks.fetchone()
        i = 1
        while raw_row:
            if i % 5 == 0:
                print(f'\t-Inserted {i} peaks...')

            # Cast the tuple to list since we need to modify it
            row = list(raw_row)

            # Convert the Well-Known Binary (WKB) to an Esri Geometry object
            row[-1] = arcpy.FromWKB(row[-1])
            iCursor.insertRow(row)
            raw_row = duck_peaks.fetchone()
            i += 1
    print(f'\tSummary: inserted {i} peaks into the Colorado_Fourteeners feature class.')

    # Get Colorado Breweries!
    sql = f"""
            SELECT
                names.primary AS Name,
                addresses[1].freeform AS Address,
                addresses[1].locality AS City,
                addresses[1].postcode as Zip,
                phones[1] as PhoneNumber,
                ST_AsWKB(geometry) AS wkb
            FROM
                read_parquet(
                    's3://overturemaps-us-west-2/release/{release}/theme=places/type=place/*',
                    filename=true, 
                    hive_partitioning=1
                )
            WHERE 
                categories.primary = 'brewery'
                AND bbox.xmin BETWEEN {colorado_bbox.xmin} AND {colorado_bbox.xmax}
                AND bbox.ymin BETWEEN {colorado_bbox.ymin} AND {colorado_bbox.ymax}
        """

    # Get DuckDB Query Relation object
    duck_breweries = conn.sql(sql)

    # Insert that data read from GeoParquet into an Esri Feature Class
    print('Creating the Colorado_Breweries feature class...')
    breweries_fc = arcpy.management.CreateFeatureclass(out_path=out_path,
                                                       out_name='Colorado_Breweries',
                                                       geometry_type='POINT',
                                                       spatial_reference=wgs84).getOutput(0)
    arcpy.management.AddField(in_table=breweries_fc, field_name='Name', field_type='TEXT', field_length=100)
    arcpy.management.AddField(in_table=breweries_fc, field_name='Address', field_type='TEXT', field_length=100)
    arcpy.management.AddField(in_table=breweries_fc, field_name='City', field_type='TEXT', field_length=20)
    arcpy.management.AddField(in_table=breweries_fc, field_name='Zip', field_type='TEXT', field_length=10)
    arcpy.management.AddField(in_table=breweries_fc, field_name='Phone_Number', field_type='TEXT', field_length=12)

    with arcpy.da.InsertCursor(breweries_fc, field_names=['Name', 'Address', 'City', 'Zip', 'Phone_Number', 'shape@']) as iCursor:
        # Get a single row as a tuple
        raw_row = duck_breweries.fetchone()
        i = 1
        while raw_row:
            if i % 50 == 0:
                print(f'\t-Inserted {i} breweries...')

            # Cast the tuple to list since we need to modify it
            row = list(raw_row)

            # Convert the Well-Known Binary (WKB) to an Esri Geometry object
            row[-1] = arcpy.FromWKB(row[-1])
            iCursor.insertRow(row)
            raw_row = duck_breweries.fetchone()
            i += 1
    print(f'\tSummary: inserted {i} breweries into the Colorado_Breweries feature class.')


if __name__ == '__main__':
    main()
