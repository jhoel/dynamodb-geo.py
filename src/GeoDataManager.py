
"""
Purpose: A wrapper on the top of DynamoDBManager for performing CRUD operation on our DynamoBD table
"""
import GeoDataManagerConfiguration
from DynamoDBManager import DynamoDBManager
from model import PutPointInput
from model import GetPointInput
from model.Covering import Covering
from s2.S2Util import S2Util
from s2.S2Manager import S2Manager
from s2sphere import LatLng as S2LatLng
EARTH_RADIUS_METERS = 6367000.0


class GeoDataManager:

    def __init__(self, config):
        self.config = config
        self.dynamoDBManager = DynamoDBManager(config)

    def put_Point(self, putPointInput):
        return self.dynamoDBManager.put_Point(putPointInput)

    def get_Point(self, getPointInput: 'getPointInput'):
        return self.dynamoDBManager.get_Point(getPointInput)

    def update_Point(self,UpdateItemInput : 'UpdateItemInput'):
        return self.dynamoDBManager.update_Point(UpdateItemInput)
        

    def delete_Point(self):
        pass

    def dispatchQueries(self, covering: 'Covering', geoQueryInput: 'GeoQueryInput'):
        """
        Generating multiple query from the covering area and running query on the DynamoDB table
        """
        ranges = covering.getGeoHashRanges(self.config.hashKeyLength)
        results = []
        for range in ranges:
            hashKey = S2Manager().generateHashKey(range.rangeMin, self.config.hashKeyLength)
            results.extend(self.dynamoDBManager.queryGeohash(
                geoQueryInput.QueryInput, hashKey, range))
        return results

    def queryRectangle(self, QueryRectangleInput: 'QueryRectangleRequest'):
        latLngRect = S2Util().latLngRectFromQueryRectangleInput(
            QueryRectangleInput)

        covering = Covering(
            self.config.S2RegionCoverer().get_covering(latLngRect))
        results = self.dispatchQueries(covering, QueryRectangleInput)
        return self.filterByRectangle(results, QueryRectangleInput)

    def queryRadius(self, QueryRadiusInput: 'QueryRadiusRequest'):
        latLngRect = S2Util().getBoundingLatLngRectFromQueryRadiusInput(
            QueryRadiusInput)
        covering = Covering(
            self.config.S2RegionCoverer().get_covering(latLngRect))
        results = self.dispatchQueries(covering, QueryRadiusInput)
        return self.filterByRadius(results, QueryRadiusInput)

    def filterByRadius(self, ItemList: 'points retrieved from dynamoDB', QueryRadiusInput: 'QueryRadiusRequest'):
        centerLatLng = S2LatLng.from_degrees(QueryRadiusInput.getCenterPoint(
        ).getLatitude(), QueryRadiusInput.getCenterPoint().getLongitude())
        radiusInMeter = QueryRadiusInput.getRadiusInMeter()
        result = []
        for item in ItemList:
            geoJson = item[self.config.geoJsonAttributeName]["S"]
            coordinates = geoJson.split(",")
            latitude = float(coordinates[0])
            longitude = float(coordinates[1])
            latLng = S2LatLng.from_degrees(latitude, longitude)
            if(centerLatLng.get_distance(latLng).radians * EARTH_RADIUS_METERS < radiusInMeter):
                result.append(item)
        return result

    def filterByRectangle(self, ItemList: 'points retrieved from dynamoDB', QueryRectangleInput: 'QueryRectangleRequest'):
        latLngRect = S2Util().latLngRectFromQueryRectangleInput(
            QueryRectangleInput)
        result = []
        for item in ItemList:
            geoJson = item[self.config.geoJsonAttributeName]["S"]
            coordinates = geoJson.split(",")
            latitude = float(coordinates[0])
            longitude = float(coordinates[1])
            latLng = S2LatLng.from_degrees(latitude, longitude)
            if(latLngRect.contains(latLng)):
                result.append(item)
        return result
