def get_query():
    query = """
    WITH
    telematics AS (
    SELECT
        display_name,
        device_time,
        positioning.position,
        base_vehicle.speed_kilometres_per_hour AS speed_km_h,
        base_vehicle.total_vehicle_distance_km AS vehicle_distance_km,
        positioning.altitude_metres AS altitude_metres,
        battery.total_battery_voltage_volts AS battery_voltage,
        battery.total_battery_current_amperes AS battery_amperes,
        (CASE
            WHEN battery.consumed_energy_j IS NULL THEN battery.total_battery_voltage_volts*battery.total_battery_current_amperes
        ELSE
        battery.consumed_energy_j
        END
        ) AS consumed_energy_J
    FROM
        `einride-dataform.reporting.clean_telematics` telematics
    WHERE
        device_time > '2021-07-01' #AND device_time < '2021-07-01'
        AND base_vehicle.vehicle_state = 'driving'
        AND positioning.position IS NOT NULL
        AND battery.total_battery_current_amperes IS NOT NULL 
        ),
    minute_telematics AS ( 
    SELECT 
    display_name AS truck,
    timestamp_trunc(device_time,MINUTE) AS date_time,
    ANY_VALUE(position) as position,
    ROUND(AVG(speed_km_h)) AS speed_km_h ,
    ROUND(MAX(vehicle_distance_km),2) as vehicle_distance_km ,
    ROUND(AVG(altitude_metres)) as altitude_m ,
    ROUND(AVG(consumed_energy_J)* 2.77778e-7,4) AS avg_kWh,
    ROUND(SUM(consumed_energy_J)* 2.77778e-7,4) AS sum_kWh,
    ROUND(MAX(vehicle_distance_km) - MIN(vehicle_distance_km),2) AS distance_travelled_km,
    COUNT(1) AS nr_samples
    FROM telematics 
    group by display_name,timestamp_trunc(device_time,MINUTE)
    )

    SELECT 
    *,
    ST_X(position) AS lon,
    ST_Y(position) AS lat,
    ROUND(sum_kWh/distance_travelled_km,1) AS kWh_km 
    from minute_telematics
    WHERE distance_travelled_km != 0 
    AND distance_travelled_km IS NOT NULL 
    AND nr_samples > 40
    AND speed_km_h > 25
    AND speed_km_h/distance_travelled_km < 100
    ORDER By date_time
    """
    return query