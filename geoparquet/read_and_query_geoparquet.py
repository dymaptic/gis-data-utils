"""=====================================================================================================================
Name: read_and_query_geoparquet.py
Purpose: Provides a hands-on example for the blog, "How to Read and Query GeoParquet in ArcGIS Pro with DuckDB".

Requirements:
    - DuckDB v1.1 which comes with ArcGIS Pro 3.5+ by default.

Author: Ed Conrad
Created: 5/27/2025
====================================================================================================================="""

import os
from collections import namedtuple

import arcpy.da
import arcpy.management
import duckdb


def main():
    import arcpy
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

    # region Get Colorado Fourteeners!
    # Overture Maps is an open data initiative that provides geospatial data in GeoParquet format,
    # which can be queried efficiently using DuckDB’s built-in Parquet and spatial extensions.
    # Dataset Schema: https://docs.overturemaps.org/schema/reference/base/land/
    # Note 1: GeoParquet stores geometries in a Well-Known Binary (WKB), which means it supports all vector
    #         geometry types defined by the OGC Simple Features standard.
    # Note 2: we leverage DuckDB's SQL dialect to select only the columns we want, passing a boundary box to limit the
    #         results to Colorado, and we make use of DuckDB's read_parquet() method and the DuckDB spatial extension's
    #         ST_AsWKB method to read the WKB
    # Docs for read_parquet() https://duckdb.org/docs/stable/data/parquet/overview#read_parquet-function
    # Docs for ST_AsWKB() https://duckdb.org/docs/stable/core_extensions/spatial/functions#st_aswkb
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
            read_parquet('s3://overturemaps-us-west-2/release/{release}/theme=base/type=land/*')
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
    print('Creating the Fourteeners feature class...')
    peaks_fc = arcpy.management.CreateFeatureclass(out_path=out_path,
                                                   out_name='Fourteeners',
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
        i = 0
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
    print(f'\tSummary: {i} points exist in the Fourteeners feature class.')
    # endregion

    # region Get Colorado Breweries!
    sql = f"""
            SELECT
                names.primary AS Name,
                addresses[1].freeform AS Address,
                addresses[1].locality AS City,
                addresses[1].postcode as Zip,
                phones[1] as PhoneNumber,
                ST_AsWKB(geometry) AS wkb
            FROM
                read_parquet('s3://overturemaps-us-west-2/release/{release}/theme=places/type=place/*')
            WHERE 
                categories.primary = 'brewery'
                AND bbox.xmin BETWEEN {colorado_bbox.xmin} AND {colorado_bbox.xmax}
                AND bbox.ymin BETWEEN {colorado_bbox.ymin} AND {colorado_bbox.ymax}
        """

    # Get DuckDB Query Relation object
    duck_breweries = conn.sql(sql)

    # Insert that data read from GeoParquet into an Esri Feature Class
    print('Creating the Breweries feature class...')
    breweries_fc = arcpy.management.CreateFeatureclass(out_path=out_path,
                                                       out_name='Breweries',
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
        i = 0
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
    print(f'\tSummary: {i} points exist in the Breweries feature class.')
    # endregion

    # region Get Colorado Road Segments!
    # According to the docs, the definition for subtype of 'road':
    # "A road segment represents a section of any kind of road, street or path, including a dedicated path for walking or cycling, but excluding a railway."
    # As of 5/28/25 the names.primary is returning segment type - which differs from the docs.
    sql = f"""
            SELECT
                names.primary as SegmentType,                
                ST_AsWKB(geometry) AS wkb
            FROM
                read_parquet('s3://overturemaps-us-west-2/release/{release}/theme=transportation/type=segment/*')
            WHERE 
                subtype = 'road'
                AND bbox.xmin BETWEEN {colorado_bbox.xmin} AND {colorado_bbox.xmax}
                AND bbox.ymin BETWEEN {colorado_bbox.ymin} AND {colorado_bbox.ymax}
        """

    # Get DuckDB Query Relation object
    duck_segments = conn.sql(sql)

    # Insert that data read from GeoParquet into an Esri Feature Class
    print('Creating the Route_Segments feature class...')
    segments_fc = arcpy.management.CreateFeatureclass(out_path=out_path,
                                                   out_name='Route_Segments',
                                                   geometry_type='POLYLINE',
                                                   spatial_reference=wgs84).getOutput(0)
    arcpy.management.AddField(in_table=segments_fc, field_name='Segment_Type', field_type='TEXT', field_length=20)
    with arcpy.da.InsertCursor(segments_fc, field_names=['shape@', 'Segment_Type']) as iCursor:
        # Get a single row as a tuple
        raw_row = duck_segments.fetchone()
        i = 0
        while raw_row:
            if i % 25_000 == 0:
                print(f'\t-Inserted {i:,} segments...')

            # Cast the tuple to list since we need to modify it
            row = list(raw_row)

            # Convert the Well-Known Binary (WKB) string to an Esri Geometry object
            row[0] = arcpy.FromWKB(row[-1])
            iCursor.insertRow(row)
            raw_row = duck_segments.fetchone()
            i += 1
    print(f'\tSummary: {i:,} polylines exist in the Route_Segments feature class.')

    # region Get Colorado Road Connectors!
    sql = f"""
            SELECT
                ST_AsWKB(geometry) AS wkb
            FROM
                read_parquet('s3://overturemaps-us-west-2/release/{release}/theme=transportation/type=connector/*')
            WHERE 
                bbox.xmin BETWEEN {colorado_bbox.xmin} AND {colorado_bbox.xmax}
                AND bbox.ymin BETWEEN {colorado_bbox.ymin} AND {colorado_bbox.ymax}
        """

    # Get DuckDB Query Relation object
    duck_connectors = conn.sql(sql)

    # Insert that data read from GeoParquet into an Esri Feature Class
    print('Creating the Route_Connectors feature class...')
    connectors_fc = arcpy.management.CreateFeatureclass(out_path=out_path,
                                                      out_name='Route_Connectors',
                                                      geometry_type='POINT',
                                                      spatial_reference=wgs84).getOutput(0)

    with arcpy.da.InsertCursor(connectors_fc, field_names=['shape@']) as iCursor:
        # Get a single row as a tuple
        raw_row = duck_connectors.fetchone()
        i = 0
        while raw_row:
            if i % 25_000 == 0:
                print(f'\t-Inserted {i:,} connectors...')

            # Cast the tuple to list since we need to modify it
            row = list(raw_row)

            # Convert the Well-Known Binary (WKB) string to an Esri Geometry object
            row[0] = arcpy.FromWKB(row[-1])
            iCursor.insertRow(row)
            raw_row = duck_connectors.fetchone()
            i += 1
    print(f'\tSummary: {i:,} points exist in the Route_Connectors feature class.')
    # endregion

    # Close DuckDB connection
    conn.close()

    # region Network Analyst section
    # Check out Network Analyst license if available. Fail if the Network Analyst license is not available.
    if arcpy.CheckExtension('Network') == 'Available':
        arcpy.CheckOutExtension('Network')
    else:
        raise arcpy.ExecuteError('Network Analyst Extension license is not available.')

    import arcpy.na
    print('Creating Route_Network...')
    arcpy.na.CreateNetworkDataset(feature_dataset=out_path,
                                  out_name='Route_Network',
                                  source_feature_class_names='Route_Segments;Route_Connectors',
                                  elevation_model='NO_ELEVATION')
    network = os.path.join(out_path, 'Route_Network')

    print('Creating Closest Facility Analysis Layers')
    closest_facility_lyr = arcpy.na.MakeClosestFacilityAnalysisLayer(network_data_source=network,
                                                                     layer_name='ClosestBreweriesToFourteeners',
                                                                     travel_direction='TO_FACILITIES',
                                                                     number_of_facilities_to_find=3).getOutput(0)
    print('Building Network...')
    arcpy.na.BuildNetwork(network)
    print('Network built!')

    # Add Breweries as the "Facilities"
    print('Adding Breweries as the Facilities')
    arcpy.na.AddLocations(
        in_network_analysis_layer=closest_facility_lyr,
        sub_layer='Facilities',
        in_table=breweries_fc,
        search_tolerance='100 Meters',  # NOTE: value determined after some trial-and-error
        match_type='MATCH_TO_CLOSEST',
        append='APPEND',
        snap_to_position_along_network='SNAP',
        snap_offset='0 Meters'
    )

    # Add Fourteeners as the "Incidents"
    print('Adding Fourteeners as the Incidents')
    arcpy.na.AddLocations(
        in_network_analysis_layer=closest_facility_lyr,
        sub_layer='Incidents',
        in_table=peaks_fc,
        search_tolerance='1500 Meters',  # NOTE: value determined after some trial-and-error
        match_type='MATCH_TO_CLOSEST',
        append='APPEND',
        snap_to_position_along_network='SNAP',
        snap_offset='0 Meters'
    )

    print('\n\nNow you need to make a manual property change to the Network Dataset that was just created.\n\n')
    print('Instructions:')
    print(f'-Expand {gdb}')
    print('-Expand the "Colorado" feature dataset')
    print('-Right-click the Route_Network dataset that was just created')
    print('-Select Properties -> Source Settings -> Group Connectivity')
    print('-Change the policy for Route_Connectors from "Honor" to "Override".\n')
    print('After making this change, uncomment the code below and run it to rebuild the Network to incorporate the change and solve.')

    print('Rebuilding Network...')
    arcpy.na.BuildNetwork(network)
    print('Network rebuilt!')

    print('Solving nearest 3 breweries to each fourteener')
    arcpy.na.Solve(closest_facility_lyr)
    print('Routes from each Fourteener to nearest 3 breweries created!')
    if arcpy.CheckExtension('Network') == 'Available':
        arcpy.CheckInExtension('Network')

    # Summarize the results!
    routes_lyr = [lyr for lyr in closest_facility_lyr.listLayers() if lyr.name == 'Routes'][0]
    arcpy.management.AddField(in_table=routes_lyr, field_name='Distance_Miles', field_type='DOUBLE')
    arcpy.management.CalculateField(
        in_table=routes_lyr,
        field='Distance_Miles',
        expression='!shape.length@meters! * 0.000621371',
        expression_type='PYTHON3'
    )
    summarize_results(routes_lyr)
    # endregion


def summarize_results(routes_lyr):
    """ Prints out the 3 nearest breweries for each fourteener. """

    summary = {}
    with arcpy.da.SearchCursor(routes_lyr, field_names=['FacilityRank', 'Name', 'Distance_Miles']) as sCursor:
        for rank, name, mileage in sCursor:
            # Split the 'Name' field into peak and brewery (format "Peak - Brewery")
            peak, brewery = name.split(' - ')

            # Initialize the peak entry if it doesn't exist
            if peak not in summary:
                summary[peak] = {}

            mileage = round(mileage, 1)

            # Store the brewery with its rank
            summary[peak][rank] = f'{brewery} ({mileage} miles)'

    for peak, ranked_breweries in summary.items():
        print(peak)
        for rank in sorted(ranked_breweries.keys()):
            print(f'\t{rank}. {ranked_breweries[rank]}')


if __name__ == '__main__':
    main()
