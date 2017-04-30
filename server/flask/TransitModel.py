import Transit
import TransitGIS
import json
import time

from geopy.distance import great_circle

CATCHMENT_DISTANCE = 0.5

class TransitModel(object):
    
    def __init__(self, ridership, region):
        self.ridership = ridership
        self.region = region
        
    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True)

def map_analysis(m):
    
    bb = TransitGIS.BoundingBox(m)
    bb.min_lat -= 0.02;
    bb.max_lat += 0.02;
    bb.min_lng -= 0.02;
    bb.max_lng += 0.02;
    
    start = time.time()
    region = TransitGIS.hexagons_bb(bb)
    condensed_region = TransitGIS.HexagonRegion()
    end = time.time()
    print "Getting hexagons took "+str(end-start)
    
    start = time.time()
    # For now just use the first service
    service = m.services[0]
    hexagon_to_station = {}
    station_to_hexagon = {}
    
    
    for station in service.stations:
        if not station.gids_known:
            for hexagon in region.hexagons:
                center = hexagon.center()
                # Look for stations within catchment.
                distance = great_circle(center, (station.location[0], station.location[1])).miles
                if (distance <= CATCHMENT_DISTANCE):
                    if hexagon in hexagon_to_station:
                        hexagon_to_station[hexagon].append(station)
                    else:
                        hexagon_to_station[hexagon] = [station]
                    if station in station_to_hexagon:
                        station_to_hexagon[station].append(hexagon)
                    else:
                        station_to_hexagon[station] = [hexagon]
                    if not condensed_region.has_hexagon(hexagon):
                        condensed_region.add_hexagon(hexagon)
        else:
            
    
    end = time.time()
    print "Analyzing hexagons took "+str(end-start)
    ridership = {}
    print "Using "+str(condensed_region.num_hexagons())+" hexagons"
    
    start = time.time()
    for hexagon in condensed_region.hexagons:
        hexagon_stations = hexagon_to_station[hexagon]
        num_stations = len(hexagon_stations)
        for station in hexagon_stations:
            demand = hexagon.population/num_stations
            if station.sid not in ridership:
                ridership[station.sid] = demand
            else:
                ridership[station.sid] += demand
                
#    for hexagon_a in condensed_region.hexagons:
#        # Get information about Hexagon A
#        hexagon_a_center = hexagon_a.center()
#        hexagon_a_stations = hexagon_to_station[hexagon_a]
#        
#        # Compare to other hexagons
#        for hexagon_b in condensed_region.hexagons:
#            if (hexagon_a != hexagon_b):
#                hexagon_b_center = hexagon_b.center()
#                hexagon_b_stations = hexagon_to_station[hexagon_b]
#                
#                # Compute demand
#                distance = great_circle(hexagon_a_center, hexagon_b_center).miles
#                demand = hexagon_a.population * max(0, 10/(hexagon_b.population - 10*distance))
#                
#                # Compute system transit cost
#                best_cost = distance
#                will_use_transit = False
#                stations = []
#                for station_a in hexagon_a_stations:
#                    for station_b in hexagon_b_stations:
#                        transit_cost = system_transit_cost(service, station_a, station_b)
#                        walk_a_cost = great_circle(hexagon_a_center, (station_a.location[0], station_a.location[1])).miles
#                        walk_b_cost = great_circle(hexagon_b_center, (station_b.location[0], station_b.location[1])).miles
#                        cost = transit_cost + walk_a_cost + walk_b_cost
#                        #print "Transit = "+str(transit_cost)+", WalkA = "+str(walk_a_cost)+", WalkB = "+str(walk_b_cost)
#                        if (cost < best_cost):
#                            best_cost = cost
#                            will_use_transit = True
#                            stations = [station_a, station_b]
#                            
#                #print "Best cost is "+str(best_cost)
#                if (will_use_transit):
#                    for station in stations:
#                        if station.sid not in ridership:
#                            ridership[station.sid] = demand
#                        else:
#                            ridership[station.sid] += demand
    
    end = time.time()
    print "Calculating ridership took "+str(end-start)
    return TransitModel(ridership, condensed_region)

def dfs(service, visited, station):
    visited[station] = True
    neighbors = service.station_neighbors(station)
    for neighbor in neighbors:
        if not visited[neighbor]:
            dfs(service, visited, neighbor)

def dijkstra(service, station):
    visited = {}
    distance = {}
    
    for s in service.stations:
        distance[s] = 0
        visited[s] = False
        
    visited[station] = True
    
    for s in service.stations:
        neighbors = service.station_neighbors(s)
        for n in neighbors:
            alt = distance[n] + neighbors[n]
            if (alt < distance[n]) or not visited[n]:
                distance[n] = alt
                visited[n] = True
                
    return distance

def system_transit_cost(service, station_1, station_2):
    distances = dijkstra(service, station_1)
    return distances[station_2]
    