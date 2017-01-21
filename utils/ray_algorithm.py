import sys
import pdb

class Point:
    def __init__(self, x, y):
        '''
        A point specified by (x,y) coordinates in the cartesian plane
        '''
        self.x = x
        self.y = y
 
class Polygon:
    def __init__(self, points):
        '''
        points: a list of Points in clockwise order.
        '''
        self.points = points

    @property
    def edges(self):
        ''' Returns a list of tuples that each contain 2 points of an edge '''
        edge_list = []
        for i,p in enumerate(self.points):
            p1 = p
            p2 = self.points[(i+1) % len(self.points)]
            edge_list.append((p1,p2))
 
        return edge_list

    def getBoundaries(self):
        ''' Returns the boundaries of the list of Points '''
        all_x = [point.x for point in self.points]
        all_y = [point.y for point in self.points]
        return [max(all_x), max(all_y), min(all_x), min(all_y)]

    def contains(self, point):
        # _huge is used to act as infinity if we divide by 0
        _huge = sys.float_info.max
        # _eps is used to make sure points are not on the same line as vertexes
        _eps = 0.00001
        
        # We start on the outside of the polygon
        inside = False
        for edge in self.edges:
            # Make sure A is the lower point of the edge
            A, B = edge[0], edge[1]
            if A.y > B.y:
                A, B = B, A

            # Make sure point is not at same height as vertex
            if point.y == A.y or point.y == B.y:
                point.y += _eps

            if (point.y > B.y or point.y < A.y or point.x > max(A.x, B.x)):
                # The horizontal ray does not intersect with the edge
                continue

            if point.x < min(A.x, B.x):
                # The ray intersects with the edge
                inside = not inside
                continue

            try:
                m_edge = (B.y - A.y) / (B.x - A.x)
            except ZeroDivisionError:
                m_edge = _huge

            try:
                m_point = (point.y - A.y) / (point.x - A.x)
            except ZeroDivisionError:
                m_point = _huge

            if m_point >= m_edge:
                # The ray intersects with the edge
                inside = not inside
                continue

        return inside

# if __name__ == "__main__":
#     q = Polygon([Point(20, 10),
#                  Point(50, 125),
#                  Point(125, 90),
#                  Point(150, 10)])
 
#     # Test 1: Point inside of polygon
#     p1 = Point(75, 50);
#     print "P1 inside polygon: " + str(q.contains(p1))
 
#     # Test 2: Point outside of polygon
#     p2 = Point(200, 50)
#     print "P2 inside polygon: " + str(q.contains(p2))
 
#     # Test 3: Point at same height as vertex
#     p3 = Point(35, 90)
#     print "P3 inside polygon: " + str(q.contains(p3))
 
#     # Test 4: Point on bottom line of polygon
#     p4 = Point(50, 10)
#     print "P4 inside polygon: " + str(q.contains(p4))

