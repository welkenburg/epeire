local tables = {}

tables.roads = osm2pgsql.define_way_table('roads', {
    { column = 'highway', type = 'text' },
    { column = 'maxspeed', type ='real' },
    { column = 'lanes', type = 'real' },
    --{ column = 'importance', type = 'real' },
    { column = 'name', type = 'text' },
    { column = 'tags', type = 'jsonb' },
    { column = 'geometry', type = 'geometry', not_null = true },
})

-- tables.intersections = osm2pgsql.define_node_table('intersections', {
--     { column = 'tags', type = 'jsonb' },
--     { column = 'degree', type = 'real' },
--     { column = 'max_speed', type = 'real' },
--     { column = 'mean_speed', type = 'real' },
--     { column = 'min_speed', type = 'real' },
--     { column = 'max_lanes', type = 'real' },
--     { column = 'mean_lanes', type = 'real' },
--     { column = 'min_lanes', type = 'real' },
--     { column = 'importance', type = 'real' },
--     { column = 'geometry', type = 'point', not_null = true },
-- })

function osm2pgsql.process_way(object)
    if object.tags.highway then
        local maxspeed = object.tags.maxspeed and tonumber(object.tags.maxspeed) or nil
        local lanes = object.tags.lanes and tonumber(object.tags.lanes) or nil
        -- local importance = object.tags.importance and tonumber(object.tags.importance) or nil
        tables.roads:insert({
            highway = object.tags.highway,
            maxspeed = maxspeed,
            lanes = lanes,
            --importance = importance,
            name = object.tags.name,
            tags = object.tags,
            geometry = object:as_linestring(),
        })
    end
end

function osm2pgsql.process_node(object)
    return
end

function osm2pgsql.process_relation(object)
    return
end