# trig.py
# a set of routines for performing various trig operations on vectors
# these routines are defined for list types, not vector types
#   reason: list types are Much more flexible!
# John Hummel, 1/16/08

import math

def sqr(value):
    # compute the square of a value
    result = value * value
    return result

def distance(V1,V2):
    # get the distance from V1 to V2
    distance = 0.0
    if len(V1) != len(V2):
        return None
    for i in xrange(len(V1)):
        distance += sqr(V1[i] - V2[i])
    return pow(distance, 0.5)

def vector_length(vector):
    # takes a vector as input and returns its length
    length = 0.0
    for i in xrange(len(vector)):
        length += sqr(vector[i])
    length = pow(length, 0.5)
    return length

def unit_vector(vector):
    # takes a vector of arbitrary length and returns a collinear vector of
    # length 1
    unit_vector = []
    length = vector_length(vector)
    if length > 0:
        for i in xrange(len(vector)):
            unit_vector.append(vector[i]/length)
    return unit_vector

def rectify_angle(angle, min_angle=0.0, max_angle=(2*math.pi)):
    # takes an angle as input and returns the same angle in range min...max
    while angle < min_angle:
        angle += max_angle
    while angle > max_angle:
        angle -= max_angle
    return angle

def vector_angle(vector):
    # takes a 2D vector as input and returns the angle, in radians, from the origin to that vector
    #
    # first, convert the vector to a unit vector by dividing elements by length
    u_vector = unit_vector(vector)
    # now compute the angle from the origin to the unit vector
    if u_vector[1] == 0:
        if u_vector[0] > 0:
            angle = 0.0
        elif u_vector[0] < 0:
            angle = math.pi
        else:
            angle = None
            print( 'ERROR in vectors.vector_angle: tried to compute angle of vector [0, 0]')
    elif u_vector[1] > 0:
        angle = math.acos(u_vector[0]) # if y > 0, then angle is arc-cos of x
    else:
        angle = 2 * math.pi - math.acos(u_vector[0]) # if y < 0 then angle is pi + arc-cos of x

    return angle

def absolute_orn_difference(orn1,orn2,range=math.pi):
    """
    Tahekes wo orientations (in radians) and returns the absolute difference between them, within the specified range.
    E.g., if the diff is 5pi/4 and the range is pi, then returns pi/4
    :param orn1: orientation 1 in radians
    :param orn2: orientation 2 in radiants
    :param range: range of comparison, i.e., gratest allowble difference (e.g., Pi or 2Pi)
    :return: absolute difference
    """
    diff = abs(orn1 - orn2)
    while diff > range:
        diff -= range
    return diff

def get_polar(cartesian, origin=[0, 0]):
    # takes cartesian coordinates, [x, y], and returns polar coordinates, [r, theta]
    polar = []  # [r, theta]
    cart = [0, 0]
    cart[0] = cartesian[0] - origin[0]
    cart[1] = cartesian[1] - origin[1]
    r = vector_length(cart)
    if r > 0:
        theta = vector_angle(cart)
    else:
        theta = 0.0
    polar.append(r)
    polar.append(theta)
    return polar

def get_cartesian(polar, origin=[0,0]):
    # takes polar coordinates, [r, theta], and returns cartesian coordinates, [x, y]
    x = origin[0] + math.cos(polar[1]) * polar[0] # x = cos(theta) * r
    y = origin[1] + math.sin(polar[1]) * polar[0] # y = sin(theta) * r
    return [x,y]
    
def get_screen_cartesian(polar, origin=[0,0]):
    # takes polar coordinates, [r, theta], and returns cartesian coordinates, [x, y]
    # EXCEPT that it turns Y upside-down, moving points that are above the origin below it, and vice-versa
    x = origin[0] + math.cos(polar[1]) * polar[0] # x = cos(theta) * r
    y = origin[1] - math.sin(polar[1]) * polar[0] # y = sin(theta) * r
    return [x,y]

