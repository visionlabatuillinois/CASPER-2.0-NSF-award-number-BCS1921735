#* Copyright 2023 The Board of Trustees of the University of Illinois. All Rights Reserved.
#
#* Licensed under the terms of the Apache License 2.0 license (the "License")
#
#* The License is included in the distribution as License.txt file.
#
#* You may not use this file except in compliance with the License.
#
#* Software distributed under the License is distributed on an "AS IS" BASIS,
#
#* WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#
#* See the License for the specific language governing permissions and limitations under the Option.

# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
# CASPER MODEL OF VISUAL SEARCH
# (Concurrent Attention: Serial and Parallel Evaluation with Relations)
# Developed by Rachel F Heaton and John E Hummel
# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *

import sys


class VisualItem(object):
    """
    This is the basic VisualItem data class for the model
    VisualItems include the target (in the display), the distractors & lures (which are in the display) and the target template (not in the display)
    """
    def __init__(self,my_list,feature_vectors,item_properties,name='',is_target=False):
        """
        :param my_list:  the list in the larger program to which this item belongs
        :param location: location on the screen, in [x,y] coordinates
        :param name: name (e.g., 'target', 'lure', 'template', etc.
        :param is_target: boolean that indicates whether this visual item is in fact the target
        """

        # the fixed parts
        self.name      = name
        self.is_target = is_target  # a boolean that specifies whether this item (in the visual display) is the target
        if my_list:
            self.index = len(my_list)
        else:
            self.index = 0

        self.item_properties      = item_properties
        self.feature_lists        = feature_vectors # this is a feature vector: will get compared to the template during search

        #self.vector_length   = 0.0 # vector length: will be computed based on what's relevant below

        # the moving parts
        self.location   = None # location on the screen, in [x,y] coordinates
        self.fix_dist   = 0.0 # distance from fixation
        self.dist_wt    = 1.0 # weighting on the acculumlator as a function of the distance from fixation
        self.integrator = 1.0 # the thing that, when it passes upper theshold, registers match (i.e., target found) and when below neg threshold registers mismatch (rejection)
        self.rejected   = False # item is rejected when integrator goes below negative threshold; ceases to be functional part of search
        self.currently_selected = False

        # for search/random selection on iteration-by-iteration basis
        self.priority   = 1.0 # this is a combination of salience, etc. When priority = 0, item has no chance of being selected; self.rejected, priority = 0
        self.subrange   = [0.0,0.0] # selection range: the subrange within [0...1] in which random.random() must fall in order for this guy to be selected

    def get_vector_length(self,relevant,relevant_weight,irrelevant_weight):
        length = 0.0

        for i in range(len(self.features)):
            if i in relevant:
                weight = relevant_weight
            else:
                weight = irrelevant_weight
            length += (self.features[i] * weight)**2
        length = pow(length,0.5)
        self.vector_length = length


    def get_fixation_distance(self,fixation):
        """
        computes the distance between the item and the fixation point
        :param fixation:
        :return:
        """
        distance = 0.0
        for i in range(len(self.location)):
            distance += (self.location[i] - fixation[i])**2
        self.fix_dist = pow(distance,0.5)

import random, math, trig


# * * * * * * * * * * * * * * * * * * * * * * * * * * *
# * * * * * * * * The Model Itself * * * * * * * * * *
# * * * * * * * * * * * * * * * * * * * * * * * * * * *


class SearchModel(object):
    def __init__(self):


        # * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
        # * * * * * * * * Major, Theory-relevant Parameters * * * * * * * * *
        # * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *

        self.LAST_MODIFIED               = "10/03/2023"
        # Search item rejection and acceptance parameters
        #self.TARGET_MATCH_THRESHOLD      = 2 # 4 # 8 # 16 # 4 # 2 # the threshold an item's integrator must exceed to be matched as the target
        self.REJECTION_THRESHOLD         = 0.001#-2.0 # -4.0 # -1.0 # -0.5  # the negative threshold an item's integrator must reach to be rejected from search altogether
        self.TARGET_ABSENT_COST          = 20 # 3 10 # just a constant added to RT due to rejections
        self.ITEM_INTEGRATOR_DECAY       = 0.5#0.5#0.01#0.5##001#0.005#05#0.02#0.01#0.02 # 1-decay is proportion preserved


        # for random sampling during inattention
        self.P_RELEVANT_SAMPLING        = 0.85
        # 0.3 for irrelevant is too high for high target-distractor similarity 06/01/2023 RFH
        # 0.1 appears to be too low with no differentiation between high and medium target-distractor similarity  06/01/2023 RFH
        self.P_IRRELEVANT_SAMPLING      = 0.15
        self.MIN_SELECTION_PRIORITY     = 0.0001#0.0001#0.1 # the smallest selection priority for non-rejected items is allowed to go
        self.POMERANTZ_UNITS            = 128

        # effect of distance between fixation and item location in the display: how much does distance from fixation impair the rate of feature sampling:
        self.DISTANCE_FALLOFF_RATE      = 1.0 # Larger means sharper falloff with distance; effect of distance modulated by DISPLAY_RADIUS
        self.LINEAR_DISTANCE_COST       = True # try a linear dropoff with distance

        # For symmetry breakign at init
        self.EXOGENOUS_CUE_NOISE        = 0.1

        # For making CASPER get distracted during attentional processing 04 Aug 2023 RFH
        self.OFF_TASK_PROBABILITY       = 0.0#1#0.99#0.1#25#25#0.1#0.05#.5#0.99

        # The effect of parallel processign needs to be greater 06 Aug 2023 RFH
        # This parameter acts as a multiplier on the match
        self.MATCH_WEIGHT               = 3#
        self.IN_TEMPLATE_WEIGHT         = 3.0
        self.OUT_OF_TEMPLATE_WEIGHT     = 0.1#0.35

        # for feature weighting under selected processing

        # operation cost parameters
        self.ATTENTION_SHIFT_COST       = 2#1#2#2#10#2#80#80#2#10#100#60#2 # how many iterations does it cost to switch attention to a new item


        # search behavior parameters
        #self.INTEGRATOR_GUIDED_PRIORITY = 1.0#0.1 #  1.0 # [0...1]: degree to which an item's integrator influences it's selection priority: influence means better-matching items are more likely to be selected for evaluation
        self.PERMIT_EYE_MOVEMENTS       = True # whether model is allowed to change fixation when it moves attention
        self.EYE_MOVEMENT_TIME_COST     = 30#60#30 #40  how long it takes to move the eyes

        # * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
        # * * * * * * * * Display Characteristics * * * * * * * * *
        # * * * * * * * * * * * * * * * * * * * * * * * * * * * * *

        self.ITEM_RADIUS               = 10  # radius of a single search item on the screen. in the case of square items, this is 1/2 the size of a side
        self.ITEM_DISTANCE             = 22  # the distance between adjacent items' upper left (x,y) coordinates: needs to be 2 * ITEM_RADIUS, plus a buffer

        self.CARTESIAN_GRID            = True#False#True#False #True#False#True  # the display grid is cartesian; if False, then it's polar

        self.DISPLAY_CENTER            = (300, 300)  # the center of the search display, in screen coordinates. will also be the initial location of fixation
        self.DISPLAY_RADIUS            = 200  # 150
        # the following is only for use with linear dropoff: the distance at which the distance weight intersects zero
        self.DISTANCE_AT_ZERO           = int(self.DISPLAY_RADIUS * 4.0)#1.5) # distance weight goes to zero at 1.5 times the radius of the display


        # * * * * * * * * * * * * * * * * * * * * * * * * * * *
        # * * * * * * * * Major Data Structures * * * * * * * *
        # * * * * * * * * * * * * * * * * * * * * * * * * * * *

        # feature dimension indices (1/17/19). Check these against make_feature_vector for consistency


        self.COLOR_DIMENSIONS = []
        self.SHAPE_DIMENSIONS = []
        self.RELATION_DIMENSIONS = []
        self.search_template  = []   # this is the template the model will search for
        self.search_items     = []   # the list of items through which the model will search; will get pared down until it's empty as items get rejected
        self.viable_items     = []   # the list of search items that are still viable
        self.rejected_items   = []   # a list of serach items that have been rejected
        self.num_lures        = 0    # hte number of non-targets in the display
        self.selected_item    = None # the item that is the current focus of attention
        self.attn_shift_timer = 0    # a timer that counts down to permit attention shift
        self.relevant         = []   # the list of relevant dimensions
        self.fixation         = self.DISPLAY_CENTER # the locatin of fixation
        self.iteration        = 0
        self.target_found     = False  # boolean indicating whether the target was found
        self.found_target     = None   # a pointer to the target that was found
        self.correct          = False # did the model get the correct answer

        # response stats
        self.num_attended        = 0 # how many things were selected during the run
        self.num_eye_movements   = 0 # how many times de the model move its eyes
        self.num_auto_rejections = 0 # how many things were rejected without being attended

        self.messages         = [] # a list of strings to tell the interface what (if anything) has happened

        self.legal_colors = ('white','black','red','green','blue','yellow','orange','pink')
        self.legal_shapes = ('vertical','horizontal','T1','T2','T3','T4','L1','L2',
                             'L3','L4','D1','D2','X', 'O', 'Q', 'P1', 'P2', 'P3','P4','P5','P6')
        self.legal_roles  = ('above', 'below', 'none')

        #TODO: Move the "theory of representation" to an external file and import
        # Item properties is a list of lists of names [[[color, shape, relational role], #]...]
        # take names for color and shape and make a corresponding feature vector
        # color vectors are [r,r,r,g,g,g,b,b,b,y,y,y]
        #                          [-------B/W-----][-------R/G------][-------B/Y-------]
        self.color_vectors = {'white' :[ 1, 1, 1,-1,-1,-1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                         'black' :[-1,-1,-1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                         'red'   :[ 0, 0, 0, 0, 0, 0, 1, 1, 1,-1,-1,-1, 0, 0, 0, 0, 0, 0],    # red = red and Not green
                         'green' :[ 0, 0, 0, 0, 0, 0,-1,-1,-1, 1, 1, 1, 0, 0, 0, 0, 0, 0], # green = green and Not red
                         'ltblue'  :[ 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 1,-1,-1,-1],  # blue = blue & not yellow
                         'blue':[ 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1,-1,-1,-1],  # blue = blue & not yellow]
                         'yellow':[ 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,-1,-1,-1, 1, 1, 1], # yellow = yellow & blue
                         'yel2ow':[ 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 0, 0, 0, 1, 1, 1],
                         'orange':[ 0, 0, 0, 0, 0, 0, 1, 1, 0,-1,-1, 0,-1, 0, 0, 1, 0, 0], # orange is 2 red, 2 not green, 1 yellow, 1 not blue
                         'pink'  :[ 1, 1, 0,-1,-1, 0, 1, 0, 0,-1, 0, 0, 0, 0, 0, 0, 0, 0],
                         'dkgrn' :[ 1, 1, 1,-1,-1, 0,-1,-1,-1, 1, 1, 1, 0, 0, 0, 0, 0, 0],
                         'brown' :[ 1, 1, 1,-1,-1, 0, 1, 1,-1,-1,-1, 1, 0, 0, 0, 0, 0, 0]}

        self.shape_vectors = {
                        'horizontal':[ 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        'vertical'  :[ 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        'T1'        :[ 1, 1, 1, 1, 0, 0, 0, 1, 0, 1, 1, 1, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0],
                        'T2'        :[ 1, 1, 1, 1, 0, 0, 0, 1, 0, 1, 1, 1, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
                        'T3'        :[ 1, 1, 1, 1, 0, 0, 0, 1, 0, 1, 1, 1, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0],
                        'T4'        :[ 1, 1, 1, 1, 0, 0, 0, 1, 0, 1, 1, 1, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0],
                        'L1'        :[ 1, 1, 1, 1, 0, 0, 0, 1, 0, 1, 1, 1, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0],
                        'L2'        :[ 1, 1, 1, 1, 0, 0, 0, 1, 0, 1, 1, 1, 1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0],
                        'L3'        :[ 1, 1, 1, 1, 0, 0, 0, 1, 0, 1, 1, 1, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0],
                        'L4'        :[ 1, 1, 1, 1, 0, 0, 0, 1, 0, 1, 1, 1, 1, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0],
                        'X'         :[ 0, 0, 0, 1, 0, 1, 1, 1, 0, 0, 0, 0, 1, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        'O'         :[ 1, 0, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        'Q'         :[ 1, 0, 0, 1, 0, 0, 0, 1, 0, 1, 1, 1, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        'DORN1'     :[ 1, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                         # 08/03/2023 RFH New compact versions of Pomerantz et al. (1977) stimuli
                        'DORN2'     :[ 0, 0, 0, 1, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0] + [0]*self.POMERANTZ_UNITS + [0]*self.POMERANTZ_UNITS,
                        'DORN6'     :[ 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0] + [0]*self.POMERANTZ_UNITS + [0]*self.POMERANTZ_UNITS,
                        'P1'        :[ 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0] + [0]*self.POMERANTZ_UNITS + [1]*self.POMERANTZ_UNITS,
                        'P2'        :[ 1, 1, 1, 1, 0, 0, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0] + [0]*self.POMERANTZ_UNITS + [1]*self.POMERANTZ_UNITS,
                        'arrow'     :[ 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0] + [1]*self.POMERANTZ_UNITS + [0]*self.POMERANTZ_UNITS,
                        'triangle'  :[ 1, 1, 1, 1, 0, 0, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0] + [0]*self.POMERANTZ_UNITS + [1]*self.POMERANTZ_UNITS,
                        'cheatXabove':[ 0, 0, 0, 1, 0, 1, 1, 1, 0, 0, 0, 0, 1, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0] + [1]*1+ [0]*1,
                        'cheatObelow':[ 1, 0, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0] + [1]*1+ [0]*1,
                        'cheatOabove':[ 1, 0, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0] + [0]*1+ [1]*1,
                        'cheatXbelow':[ 0, 0, 0, 1, 0, 1, 1, 1, 0, 0, 0, 0, 1, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0] + [0]*1+ [1]*1,
                        'nocheatX': [0, 0, 0, 1, 0, 1, 1, 1, 0, 0, 0, 0, 1, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0] + [0] * 1 + [0] * 1,
                        'nocheatO': [1, 0, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0] + [0] * 1 + [0] * 1}



        #print("cheatXabove " + str(self.shape_vectors['cheatXabove']))


        self.relation_vectors = {'above': [1, 1, 0, 0],
                                 'below': [0, 0, 1, 1],
                                 'none' : [0, 0, 0, 0]}

        # DEFAULTS
        # FOR SIMULATION 1: TREISMAN & GELADE (1980),
        # SIMULATION 2: WOLFE ET AL. (1989),
        # SIMLATION 4: TREISMAN & SOUTHER (1985)
        # SIMULATION 6: LOGAN (1994) WITH MULTICOLOR STIMULI
        # SIMULATION 7: LOGAN (1994) WITH MONOCOLOR STIMULI

        '''
        dim_index = 0
        for i in range(len(self.color_vectors['red'])):
            self.COLOR_DIMENSIONS.append(dim_index)
            dim_index += 1

        for i in range(len(self.shape_vectors['X'])):
            self.SHAPE_DIMENSIONS.append(dim_index)
            dim_index += 1

        for i in range(len(self.relation_vectors['above'])):
            self.RELATION_DIMENSIONS.append(dim_index)
            dim_index += 1

        self.non_relation_dimensions = self.COLOR_DIMENSIONS + self.SHAPE_DIMENSIONS
        self.salience = [1] * 18 + [1] * 27

        # SIMULATION 3: BUETTI ET AL. (2016)
        elif self.SIM_ID == 3:

            dim_index = 0
            for i in range(len(self.color_vectors['red'])):
                self.COLOR_DIMENSIONS.append(dim_index)
                dim_index += 1

            for i in range(len(self.shape_vectors['X'])):
                self.SHAPE_DIMENSIONS.append(dim_index)
                dim_index += 1

            for i in range(len(self.relation_vectors['above'])):
                self.RELATION_DIMENSIONS.append(dim_index)
                dim_index += 1

            self.non_relation_dimensions = self.COLOR_DIMENSIONS + self.SHAPE_DIMENSIONS
            self.salience = [1] * 18 + [1.5] * 27

        # SIMULATION 5: POMERANTZ ET AL. (1977)
        elif self.SIM_ID == 5:
            dim_index = 0
            for i in range(len(self.color_vectors['red'])):
                self.COLOR_DIMENSIONS.append(dim_index)
                dim_index += 1

            for i in range(len(self.shape_vectors['P1'])):
                self.SHAPE_DIMENSIONS.append(dim_index)
                dim_index += 1

            for i in range(len(self.relation_vectors['above'])):
                self.RELATION_DIMENSIONS.append(dim_index)
                dim_index += 1

            self.non_relation_dimensions = self.COLOR_DIMENSIONS + self.SHAPE_DIMENSIONS
            self.salience = [1] * 18 + [1] * 27 + [1] * self.POMERANTZ_UNITS + [1] * self.POMERANTZ_UNITS

        # SIMULATION 8A: MULTICOLOR RELATIONAL SEARCH (EXPERIMENT 1A, 1B) WITH EMERGENT FEATURE DEFAULT SALIENCE
        # OR
        # SIMULATION 9A: MONOCOLOR RELATIONAL SEARCH (EXPERIMENT 2A, 2B) WITH EMERGENT FEATURE DEFAULT SALIENCE
        # OR
        # SIMULATION 9B: MONOCOLOR RELATIONAL SEARCH (EXPERIMENT 2A, 2B) WITH EMERGENT FEATURE DEFAULT SALIENCE
        elif self.SIM_ID in {8, 10, 11}:
            dim_index = 0
            for i in range(len(self.shape_vectors['cheatXabove'])):
                self.SHAPE_DIMENSIONS.append(dim_index)
                dim_index += 1
            for i in range(len(self.relation_vectors['above'])):
                self.RELATION_DIMENSIONS.append(dim_index)
                dim_index += 1

            self.non_relation_dimensions = self.COLOR_DIMENSIONS + self.SHAPE_DIMENSIONS
            self.salience = [1] * 18 + [1] * 27 + [1] * 2

        # SIMULATION 8B: MULTICOLOR RELATIONAL SEARCH (EXPERIMENT 1) WITH EMERGENT FEATURE REDUCED SALIENCE
        elif self.SIM_ID == 9:
            dim_index = 0
            for i in range(len(self.shape_vectors['cheatXabove'])):
                self.SHAPE_DIMENSIONS.append(dim_index)
                dim_index += 1
            for i in range(len(self.relation_vectors['above'])):
                self.RELATION_DIMENSIONS.append(dim_index)
                dim_index += 1

            self.non_relation_dimensions = self.COLOR_DIMENSIONS + self.SHAPE_DIMENSIONS
            self.salience = [1] * 18 + [1] * 27 + [0.33] * 2

        # SIMULATION 10: SPACED OUT MULTICOLOR RELATIONAL SEARCH (EXPERIMENT 4) WITH EMERGENT FEATURE REDUCED SALIENCE
        elif self.SIM_ID == 12:
            dim_index = 0
            for i in range(len(self.shape_vectors['cheatXabove'])):
                self.SHAPE_DIMENSIONS.append(dim_index)
                dim_index += 1
            for i in range(len(self.relation_vectors['above'])):
                self.RELATION_DIMENSIONS.append(dim_index)
                dim_index += 1

            self.non_relation_dimensions = self.COLOR_DIMENSIONS + self.SHAPE_DIMENSIONS
            self.salience = [1] * 18 + [1] * 27 + [0.33] * 2
            self.P_RELEVANT_SAMPLING = 0.95



        #self.salience = [1] * 18 + [1] * 27
        # Salience vector for Buetti et al simulation
        #self.salience = [1] * 18 + [1.5] * 27
        # Salience vector for Pomerantz et al simulation
        #self.salience = [1] * 18 + [1] * 27 + [1]*self.POMERANTZ_UNITS + [1]*self.POMERANTZ_UNITS

        # Salience vector for Multicolor relations simulation
        #self.salience = [1] * 18 + [1] * 27 + [0.33] * 2
        #self.salience = [1] * 18 + [1] * 27 + [0.33] * 2

        # Salience vector for Monocolor relations simulation
        #self.salience = [1] * 18 + [1] * 27 + [1] * 2
'''


    def make_feature_vectors(self, item_properties):





        # target : [[[p1-1c ,p1-1s, p1-1r][p1-2c, p1-2s, p1-2r],[p1-3c,p1-3s,p1-3r]], 'tp/a']
        # distractors : [[[[p1-1c ,p1-1s, p1-1r][p1-2c, p1-2s, p1-2r],[p1-3c,p1-3s,p1-3r]], '#p1'] , [[[p2-1c ,p2-1s, p2-1r][p2-2c, p2-2s, p2-2r],[p2-3c,p2-3s,p2-3r]], '#p2']]

        all_feature_vectors = [] # a list of the form [[color, shape, relational role],[color, shape, relational role]...], #]
        # # print("DEBUG item properties in make_feature_vectors(): " + str(item_properties))
        for element in item_properties[0]:  # each element is a list of the form [[color, shape, relational role], #]
            # # print("DEBUG element: " + str(element))
            color_vector = self.color_vectors[element[0]] # color
            shape_vector = self.shape_vectors[element[1]] # shape
            relation_vector = self.relation_vectors[element[2]] # relational role
            feature_vector = []
            feature_vector.extend(color_vector)
            feature_vector.extend(shape_vector)
            feature_vector.extend(relation_vector)
            all_feature_vectors.append(feature_vector)

        #print("VERIF all_feature_vectors from make_feature_vectors() : " + str(all_feature_vectors))
        return all_feature_vectors


    def add_search_items(self,num, item_properties, name = '',is_target=False):
        """
        creates a (subset of a) search display: makes num items of color and shape
        num: how many to make
        color: what color to make them
        shape: what shape to make them
        disply_list: the larger search display list to which they will be added
        :return: the list of items in the display
        """
        # get the feature vector
        features = self.make_feature_vectors(item_properties)
        # make the required number of these guys
        for i in range(num):
            # my_list,feature_vector,color_name='',shape_name='',name='',is_garget=False
            self.search_items.append(VisualItem(self.search_items,features,item_properties,name, is_target))




    # * * * * * * * * * * * * * * * * * * * * * * * * * * *
    # * * * * * * * * * Search Display * * * * * * * * * *
    # * * * * * * * * * * * * * * * * * * * * * * * * * * *

    def make_cartesian_locations(self):
        """
        Makes a list of locations on an (x,y) cartesian grid for stimuli. 
        param: display_space: a rectangle [center_x,center_y,half_width], center_x and center_y are the coordinates of the center of the display and half_width is half the width of the full display (like a radius)
        :return: a list of locations in a randomized order (random.shuffle()); each location is only (upper_left,upper_right), expressed in screen coordinates
        """
        locations = []
        min_x = self.DISPLAY_CENTER[0] - self.DISPLAY_RADIUS
        max_x = min_x + 2*self.DISPLAY_RADIUS - 2*self.ITEM_RADIUS
        min_y = self.DISPLAY_CENTER[1] - self.DISPLAY_RADIUS
        max_y = min_y + 2*self.DISPLAY_RADIUS - 2*self.ITEM_RADIUS

        xpos = min_x # start in upper left: center_x minus half_width
        while (xpos+self.ITEM_RADIUS) <= max_x: # while you're not wider than the display...
            ypos = min_y  # start in upper left: center_y minus half_width
            while (ypos+self.ITEM_RADIUS) <= max_y: # while you're not taller than the display
                location = [xpos,ypos]
                locations.append(location)
                ypos += self.ITEM_DISTANCE
                # DIAG
                # print( location)
            xpos += self.ITEM_DISTANCE

        # the locations are constructed: shuffle and return them
        random.shuffle(locations)
        return locations

    def make_polar_locations(self, dense = False):
        """
        makes a list oflocations arrayed in a polar fashion around the center od the display for for stimuli
        :param dense means fill as many angles as possible; if not, then increment abgle by Pi/8 for all radii
        :return: a list of locations in a randomized order (random.shuffle()); each location is (upper_left,upper_right), expressed in screen (cartesian) coordinates
        """
        locations = []
        # add the cenetr of the display
        # locations.append([DISPLAY_CENTER[0]-ITEM_DISTANCE,DISPLAY_CENTER[1]-ITEM_DISTANCE])

        # DIAG
        # if GRAPHIC:
        #     # show center of display
        #     pygame.draw.circle(screen,BLACK,DISPLAY_CENTER,2,0)

        # now iterate through radii in increments of ITEM_DISTANCE
        radius = self.ITEM_DISTANCE * 2
        while radius+self.ITEM_RADIUS < self.DISPLAY_RADIUS:
            angle = 0
            if dense: # fill as many angles as possible
                # figure out the angle_increment for this radius: it is the fraction of the circumference taken by the item width
                circumference = 2 * math.pi * radius
                distance_increment = self.ITEM_DISTANCE/circumference  # dist. increment is the fraction of the circle you can move
                angle_increment = distance_increment * 2 * math.pi # angle increment is that, expressed in radians basically, the angle increment is set to the number of items that can fit inside the circumference
            else:  # not dense: only fill angles in increments of Pi/8
                angle_increment = math.pi/4.0
            while angle < 2 * math.pi:
                [real_x,real_y] = trig.get_cartesian([radius,angle],self.DISPLAY_CENTER) # get the cartesian coordinates at this radius and angle
                location = [int(round(real_x))-self.ITEM_RADIUS,int(round(real_y))-self.ITEM_RADIUS]                # round it off to integer values and offset by item radius to center @ location
                locations.append(location)                                                                 # and add it to the list
                angle += angle_increment                                                                   # and increment the angle
            if dense: # increment radius by minimum amount
                radius += self.ITEM_DISTANCE
            else:
                radius *= 1.5 # += ITEM_DISTANCE # * 1.5

        # the locations are all made: shuffle & return them
        random.shuffle(locations)
        return locations

    def assign_locations(self):
        """
        assign screen locations to the search items
        :return: the search display, once items have been assigned
        """
        if self.CARTESIAN_GRID:
            locations = self.make_cartesian_locations()
        else:
            locations = self.make_polar_locations()
        # at this point, locations is a randomly ordered set of locations in either cartesian or polar space
        # now iterate through the search_display and assugn these locations ot the search items
        for item in self.search_items:

            item.location = locations.pop(0)


    # * * * * * * * * * * * * * * * * * * * * * * * * * * *
    # * * * * * Major Functions: Search Operations * * * * *
    # * * * * * * * * * * * * * * * * * * * * * * * * * * *

    def init_search(self, verbose_title=''):
        """
        inits all major variables at the start of the search: this called only once per search run
        :return:
        """
        self.viable_items     = list(self.search_items)   # the list of search items that are still viable
        self.rejected_items   = []   # a list of serach items that have been rejected
        self.selected_item    = None # the item that is the current focus of attention
        self.attn_shift_timer = 0    # a timer that counts down to permit attention shift
        self.fixation         = self.DISPLAY_CENTER # the locatin of fixation
        self.iteration        = 0
        self.target_found     = False  # boolean indicating whethr the target was found
        self.found_target     = None   # a pointer to the target that was found
        self.correct          = False # did the model get the correct answer

        self.clear_messages()
        self.messages.append(verbose_title)
        self.messages.append('Fixation at '+str(self.fixation))

        # init the response stats
        self.num_attended        = 0 # how many things were selected during the run
        self.num_eye_movements   = 0 # how many times de the model move its eyes
        self.num_auto_rejections = 0 # how many things were rejected without being attended

        # init the working parts on all the search items
        for item in self.search_items:
            # the working parts
            item.location           = None # location on the screen, in [x,y] coordinates
            item.fix_dist           = 0.0 # distance from fixation
            item.dist_wt            = 1.0 # weighting on the acculumlator as a function of the distance from fixation
            item.integrator         = 1.0 + random.random()*self.EXOGENOUS_CUE_NOISE # the thing that, when it passes upper theshold, registers match (i.e., target found) and when below neg threshold registers mismatch (rejection)
            item.rejected           = False # item is rejected when integrator goes below negative threshold; ceases to be functional part of search
            item.currently_selected = False
            item.priority           = 1.0 # this is a combination of salience, etc. When priority = 0, item has no chance of being selected; self.rejected, priority = 0
            item.subrange           = [0.0,0.0] # TODO WAIT HUH? SO NEVER? # selection range: the subrange within [0...1] in which random.random() must fall in order for this guy to be selected

        # and assign the items random locations in the display
        self.assign_locations()

        # and set the initial fixation distance weights (new, 2/12/19:previously wasn't doing this till eye movement)
        for item in self.search_items:
            distance = 0
            for i in range(len(self.fixation)):
                distance += (self.fixation[i] - item.location[i])**2
            item.fix_dist = pow(distance,0.5)

            # and compute distance_wt: the weighting on the accumuators as a function of fixation distance
            if self.LINEAR_DISTANCE_COST:
                item.dist_wt = 1.0 - (float(item.fix_dist)/self.DISTANCE_AT_ZERO)
                # print(item.dist_wt)
                if item.dist_wt < 0.0: item.dist_wt = 0.0
            else: # original (pre-2/14/19) nonlinear distance cost
                scaled_distance = self.DISTANCE_FALLOFF_RATE * (float(item.fix_dist)/self.DISPLAY_RADIUS)
                item.dist_wt = 1.0/(1.0 + scaled_distance)


    def randomly_select_item_with_distance(self):
        #print("Calling distance luce")
        priority_sum = 0.0
        #print(len(self.viable_items))
        for item in self.viable_items: # self.search_items:
            # make sure rejected items stay rejected
            if item.rejected: item.priority = 0
            #print("Item " + str(item.index) + " priority " + str(item.priority))
            priority_sum += item.priority*item.dist_wt
            item.currently_selected = False # init all to False at this point

        # 2) assign each item a subrange: a subset of the range [0...1] whose width is proportional to item_priority/priority_sum
        if priority_sum > 0:
            range_bottom = 0.0
            for item in self.viable_items: # self.search_items:
                range_top = range_bottom + (item.priority*item.dist_wt)/priority_sum # range width = range_bottom...range_top = item.priority/priority_sum
                #if range_bottom == range_top:
                    #print(str(range_bottom))
                    #print(str(range_top))
                    #print(item.priority)
                    #print(item.dist_wt)
                    #exit()
                item.subrange = [range_bottom,range_top]
                range_bottom = range_top

        # 3) get a random number in [0...1] and select as chosen the item whose subrange includes that number
        the_number = random.random()
        for item in self.viable_items: # self.search_items:

            #print(item.subrange)
            if the_number >= item.subrange[0] and the_number < item.subrange[1]:
                item.currently_selected = True
                self.num_attended += 1 # increment the number of things attended
                return item

        # 4) if you get to this point, you found nothing: return None
        return None

    # def check_for_target_absent(self):
    #     target_absent = True
    #     for item in self.viable_items:
    #         if not item.rejected:
    #             target_absent = False
    #             return(target_absent)
    #     return(target_absent)

    def randomly_select_item(self):
        # randomly selects one viable search item based on all viable items' priorities
        # 1) calculate the sum of all items' priorities
        priority_sum = 0.0
        for item in self.viable_items: # self.search_items:
            # make sure rejected items stay rejected
            if item.rejected: item.priority = 0
            priority_sum += item.priority
            item.currently_selected = False # init all to False at this point

        # 2) assign each item a subrange: a subset of the range [0...1] whose width is proportional to item/priority/priority_sum
        if priority_sum > 0:
            range_bottom = 0.0
            for item in self.viable_items: # self.search_items:
                range_top = range_bottom + item.priority/priority_sum # range width = range_bottom...range_top = item.priority/priority_sum
                item.subrange = [range_bottom,range_top]
                range_bottom = range_top

        # 3) get a random number in [0...1] and select as chosen the item whose subrange includes that number
        the_number = random.random()
        for item in self.viable_items: # self.search_items:
            if the_number >= item.subrange[0] and the_number < item.subrange[1]:
                item.currently_selected = True
                self.num_attended += 1 # increment the number of things attended
                return item

        # 4) if you get to this point, you found nothing: return None
        return None

    def random_sample_feature_match(self,item):
        vect = item.feature_lists

        # for unattended processing: decide vect1-vect2 similarity by randomly sampling
        #   dimensions
        # return num_matches - num_mismatches
        match = 0
        # len1 = 0
        # len2 = 0
        sample_sum = 0

        # DIAG
        sampled_relevant = []
        sampled_irrelevant = []
        # end DIAG

        # For each part in the search template (if it has multiple parts)
        for feature_list in self.search_template.feature_lists:

            # This is parallel processing, so the notion of relations shouldn't apply at this point
            # For ever feature in the part
            for i in range(len(self.non_relation_dimensions)):
                do_sample = False
                # Determine whether the feature will be sampled, as determined by probabilities based on relevance
                if i in self.relevant:
                    do_sample = random.random() < self.P_RELEVANT_SAMPLING
                    # DIAG
                    if do_sample: sampled_relevant.append(i)
                    # end DIAG
                elif i in self.irrelevant:
                    do_sample = random.random() < self.P_IRRELEVANT_SAMPLING
                    # DIAG
                    if do_sample: sampled_irrelevant.append(i)
                    # end DIAG
                # else: do_sample = False
                if do_sample:
                    #sample_num += 1 # This count is no longer needed

                    # vect is the set of item feature lists. For each feature list in the item
                    for v in vect:
                        #This version counts features in the search items even if they're not in the search template
                        #If the feature is not in the search template part but it's in the item part, decrement
                        if feature_list[i] == 0:
                            if v[i] != 0: match -= self.OUT_OF_TEMPLATE_WEIGHT*self.salience[i]

                        else:
                            if feature_list[i] == v[i]:
                                # If the feature in the search template part and the feature in the item part match, increment
                                match += self.IN_TEMPLATE_WEIGHT*self.salience[i]#3.0*self.salience[i]

                            else:
                                # If the feature in the search template part and the feature in the item part mismatch, decrement
                                match -= self.IN_TEMPLATE_WEIGHT*self.salience[i]#3.0*self.salience[i]
                        '''
                        # This version only counts features in the search template
                        if feature_list[i]:
                            if feature_list[i] == v[i]:
                                match += 1.0 * self.salience[i]  # 3.0*self.salience[i]
                            else:
                                match -= 1.0 * self.salience[i]  # 3.0*self.salience[i]
                        '''

        #print("Match is " + str(match))
        # now normalize the match score by the max possible

        relevant_sum = 0
        for i in self.relevant:
            #print(i)
            #print(self.salience[i])
            relevant_sum += self.salience[i]

        #adjust for relations
        #relevant_sum *= len(self.search_template.feature_lists)
        #relevant_sum *= len(vect)
        #print(relevant_sum)
        #print(len(self.relevant))
        #if len(self.relevant) != 0: match /= (len(self.relevant)/3.0) # 3.0 because this is the weight of the best match in the match calculation
        match *= self.MATCH_WEIGHT
        if len(self.relevant) != 0: match /= (relevant_sum)  # 3.0 because this is the weight of the best match in the match calculation
        #if sample_num != 0: match/= sample_num
        #print("Match final is " + str(match))

        '''
        # DIAG
        if item.is_target:
            print('----- For Target -----')
            print('      Relevant features sampled = '+str(sampled_relevant))
            print('      Irrelevant features sampled = '+str(sampled_irrelevant))
            print('      Match (normalized) = '+str(match))
        elif item.index == 1:
            print('----- For Distractor 1 -----')
            print('      Relevant features sampled = '+str(sampled_relevant))
            print('      Irrelevant features sampled = '+str(sampled_irrelevant))
            print('      Match (normalized) = ' + str(match))
        # end DIAG
        '''
        return match



    def process_parallel(self,item):
        # this is the processing that happens in parallel across all items
        # this method will be called in a loop
        # get item/target similarity
        # similarity = feature_similarity(item.features, template.features)
        # relevant is the set of relevant dimensions, e.g., color or shape
        similarity = self.random_sample_feature_match(item) #used to be just the feature list, now pass the whole item

        # use similarity to update item threshold
        #ToDo: Should parallel computation be affected by distance from fixatrion? If so, should it be as much as seective processing is?
        item.integrator += similarity * random.random() * item.dist_wt

        # 06/01/2023 RFH: don't actually let items go below rejection threshold, instead let them be very small
        # and unlikely to be selected by the Luce's choice calculation
        if item.integrator < self.MIN_SELECTION_PRIORITY:
            item.integrator = self.MIN_SELECTION_PRIORITY
        # 1/18/18: experiment: update priority based on integrator
        item.priority = item.integrator # Try this and see how it works 10/23/19 RFH
        #item.priority += item.integrator * self.INTEGRATOR_GUIDED_PRIORITY
        # if item.priority < self.MIN_SELECTION_PRIORITY:
        #     print("Priority less than minimum ")
        #     item.priority = self.MIN_SELECTION_PRIORITY
        #     print("Priority " + str(item.priority))


        # determine whether rejected
        if item.integrator < self.REJECTION_THRESHOLD:
            # mark the item as rejected
            item.rejected = True
            item.priority = 0.0

            # for reporting
            self.make_message('----------'+str(item.index)+' rejected in parallel phase---------')

            self.num_auto_rejections += 1  # record that this was rejected without being attended
            #print("Item " + str(item.index) + " rejected in parallel phase with priority " + str( item.priority) +  " on iteration " + str(self.iteration))



    def process_selected_item_better(self):
        """
        # this is what happens when an item is randomly selected:
        # It is compared to the target template and it is rejected as a non-target on any mismatch. ANY!
        """

        # New algorithm for relational search 08/02/2020

        # If there is a length mismatch, then instant mismatch
        if len(self.search_template.feature_lists) != len(self.selected_item.feature_lists):
            self.selected_item.rejected = True
            self.selected_item.priority = 0.0
            self.selected_item.currently_selected = False
            self.make_message('Selected item '+str(self.selected_item.index)+' rejected')
            self.selected_item = None
            # Waste no more time
        # Randomly choose feature list from the template
        else:

            # We want to randomly choose a feature list from the template. We make a new list of indices based on the
            # length of the feature list, then pop the indices to access the item feature_lists vector
            num_features = len(self.selected_item.feature_lists)
            list_indices = [i for i in range(num_features)]
            found_match = []
            random.shuffle(list_indices)
            for index in list_indices:   # for each of the feature vectors in the selected item (in random order because of shuffle)
                feature_list_match = False
                for template_feature_list in self.search_template.feature_lists: # for each feature list in the search template
                    mismatches = 0
                    for feature in range(len(template_feature_list)):
                        if self.selected_item.feature_lists[index][feature] != template_feature_list[feature]:
                            mismatches += 1
                    if mismatches == 0:
                        feature_list_match = True
                found_match.append(feature_list_match)
            # print("VERIF found_match " + str(found_match))
            if all(found_match) == False:
                #if random.random() > self.OFF_TASK_PROBABILITY:
                self.selected_item.rejected = True
                #print("Rejected item on simulation step " + str(self.iteration))
                self.selected_item.priority = 0.0
                self.selected_item.currently_selected = False
                self.make_message('Selected item '+str(self.selected_item.index)+' rejected')

                self.selected_item = None
            else:
                self.target_found = True
                self.found_target = self.selected_item
                self.make_message('Selected item ' + str(self.selected_item.index) + ' has been identified as the target!')



    def fixate_selected(self):
        """
        changes the fixation point to the location of the selected item and recomputes everyone's distance from fixation    
        """

        distance_to_selected = 0
        for i in range(len(self.fixation)):
            distance_to_selected += (self.fixation[i] - self.selected_item.location[i]) ** 2
        fix_to_selected_dist = pow(distance_to_selected, 0.5)

        if self.LINEAR_DISTANCE_COST:
            dist_wt = 1.0 - (float(fix_to_selected_dist) / self.DISTANCE_AT_ZERO)
            if dist_wt < 0.0: dist_wt = 0.0
        #    print("dist_wt = " + str(dist_wt))
        else:  # original (pre-2/14/19) nonlinear distance cost
            scaled_distance = self.DISTANCE_FALLOFF_RATE * (float(fix_to_selected_dist) / self.DISPLAY_RADIUS)
            dist_wt = 1.0 / (1.0 + scaled_distance)

        if random.random() < dist_wt:#(1.0 - dist_wt):
            self.fixation = list(self.selected_item.location)
            # 3.A.1.1) pay the eye movement cost:
            # Simply adding the iterations in this way is tantamount to suspending all
            #   processing, including unattended processing, during the eye movement
            self.iteration += self.EYE_MOVEMENT_TIME_COST
            #print("I MOVED MY EYES")
        #else:
        #    print("I DIDN'T MOVE MY EYES")




        self.make_message('Fixation moved to '+str(self.fixation))
        self.num_eye_movements += 1  # how many times de the model move its eyes

        for item in self.search_items:
            distance = 0
            for i in range(len(self.fixation)):
                distance += (self.fixation[i] - item.location[i])**2
            item.fix_dist = pow(distance,0.5)

            # and compute distance_wt: the weighting onthe accumuators as a function of fixation distance
            # and compute distance_wt: the weighting on the accumuators as a function of fixation distance
            if self.LINEAR_DISTANCE_COST:
                item.dist_wt = 1.0 - (float(item.fix_dist)/self.DISTANCE_AT_ZERO)
                if item.dist_wt < 0.0: item.dist_wt = 0.0
            else: # original (pre-2/14/19) nonlinear distance cost
                scaled_distance = self.DISTANCE_FALLOFF_RATE * (float(item.fix_dist)/self.DISPLAY_RADIUS)
                item.dist_wt = 1.0/(1.0 + scaled_distance)

    def update_viability(self):
        """
        moves rejected items to the rejected_items list leaving only viable items (.rejected = False) to the search_items list
        :return:
        """
        still_viable_items   = [] # a holding pen for those items that are still viable
        # go through all items and either put them in the (temporary) viable list or in the rejected list
        for item in self.viable_items:
            if item.rejected:
                item.currently_selected = False
                self.rejected_items.append(item)
            else:
                still_viable_items.append(item)
        # now reset self.search_items to be just the viable ones
        self.viable_items = still_viable_items
        #print("Viable remaining " + str(len(self.viable_items)))


    def run_search_step(self):
        """
        runs one step of the search: this will be called repeatedly by the interface
        """

        all_done = False # all done with search
        # update iteration counter
        self.iteration += 1

        # On Each Iteration...
        self.messages.append('\n* * * Iteration '+str(self.iteration)+' * * *')

        for item in self.viable_items:
            #print("Item " + str(item.index) + " has priority " + str(item.priority) + " before parallel processing on iteration " + str(self.iteration))

            item.integrator *= (1.0 - self.ITEM_INTEGRATOR_DECAY)
        # 0) process all the remaining (viable) in parallel
        for item in self.viable_items: # self.search_items:
            if not item.rejected:
                self.process_parallel(item)

        # 1) move all the rejected items to the self.rejected_items list -- that's in update_viability
        self.update_viability()

        # 2) if nothing is yet the focus of attention, then randomly select one item
        #    from the set remaining...
        if not self.selected_item:
            #print("calling random selction with distance")
            self.selected_item = self.randomly_select_item_with_distance()


            # if you found something, then start the timers to shift attention and move the eyes
            if self.selected_item:
                # start the timer to actually get attention to selected item
                self.attn_shift_timer = self.ATTENTION_SHIFT_COST
                # 3.A.1) move the eyes to the item (if allowed)
                if self.PERMIT_EYE_MOVEMENTS:
                    # 3.A.1.2) and fixate the attended item
                    self.fixate_selected()
                # report that a new thing has been selected
                self.make_message('Moving attention to item '+ str(self.selected_item.index)+' at '+str(self.selected_item.location))

        # 3) process selected item
        if self.selected_item:

            # 3.A) if the timer has counted down to zero, then attention has just now gotten to
            #      the selected item...
            if self.attn_shift_timer == 0:
                self.make_message('Attention arrived on item '+str(self.selected_item.index))

                # 3.A.2) process the selected item
                self.process_selected_item_better()
                # 3.A.3) decrement the attention_shift_timer to -1 so that
                #        3.A.1 is not repeated next time
                self.attn_shift_timer = -1

            # 3.B) if the timer is less than zero, then you're already at the selected item:
            #      just process it
            #elif self.attn_shift_timer < 0:
            #    self.process_selected_item_better()

            # 3.C) otherwise, the timer is still > 0: just decrement the timer
            else:
                self.attn_shift_timer -= 1


        # 4) move all the rejected items to the self.rejected_items list -- that's in update_viability
        self.update_viability()

        # 5) look to see whether you're done. you're done when
        # (a) you've found the target, or
        # (b) there are no non-rejected items in the display. if not, halt and declare no target
        if self.target_found:
            self.found_target = self.selected_item
            #self.iteration += self.TARGET_PRESENT_COST
            self.make_message('Target Found! Item ' + str(self.selected_item.index) + ', '+self.selected_item.name+ ' at ' + str(self.selected_item.location) + ' on iteration '+str(self.iteration)+'\n')
            all_done = True
            #print("* * * * * * * * ")

        #target_absent = self.check_for_target_absent()
        #if target_absent:
        #    self.iteration += self.TARGET_ABSENT_COST
        #    self.make_message('I have concluded the Target is Absent on iteration ' + str(self.iteration) + '\n')
        #    all_done = True

        elif len(self.viable_items) == 0:
            self.iteration += self.TARGET_ABSENT_COST
            self.make_message('I have concluded the Target is Absent on iteration ' + str(self.iteration) + '\n')
            all_done = True

        return all_done # let whoever called you know whether the simulation is done

    def analyze_result(self):
        """
        at the end of the search, determines whether it got the search right or wrong
        :return: 
        """

        if self.target_found:
            #print('Found target!')
            # you found something. make sure it's the target
            self.correct = self.found_target.is_target

        else:
            # you found nothing. make sure there was no target in the display
            correct = True
            for item in self.search_items:
                if item.is_target:
                    correct = False # there was a target and you missed it
                    break
            self.correct = correct

    def run_whole_search(self,verbose_title=''):
        """
        this runs the whole search. if you're calling ths, then you aren't using graphics
        If you wanna use graphics, then use the interface to run the search one iteraiton at a time
        :return: 
        """
        self.init_search(verbose_title)
        all_done = False
        while not all_done:
            all_done = self.run_search_step()
        self.analyze_result() # determine whether your response was correct

    def create_simulation(self,target,non_targets,relevant=None):
        """
        Creates the data structures for a simulation (or batch run thereof)
        :param target: a list of the form ['color','shape',n] e.g., ['red','vertical',1] is target present, red vertical
        ['red','vertical',0] is target absent, red vertical
        :param non_targets: a list of lists of the same form ['color','shape',n], e.g.,
        [['red','horizontal',4],['green','vertical',4]] means 4 red horizontals and 4 green verticals,
        :param relevant: which dimensions are relevant. if None, then determine automatically
        otherwise, relevant, set as, e.g., COLOR_DIMENSIONS + SHAPE_DIMENSIONS, specifies it
        """

        # 1) make the search template...
        # Target is of form [[color,shape, rel_role], [color, shape, rel_role]]
        self.search_template = VisualItem(None, self.make_feature_vectors(target), target)  # target[0] is color, target[1] is shape


        # 3) make the search items
        self.search_items = []

        # 3.1) if target present, then add the target
        # target looks like [[color, shape, rel role], 1]
        # # print("DEBUG target in create_simulation() " + str(target))
        if target[1] == 1:  # if there's a non-zero value for num_targets...(There can only be one target)
            # ... then add the target to the display as the 0th item:
            #                make_search_items(existing_list,num,color,shape,name = '',is_target=False)
            name = 'Target=' + str(target[0]) + '_' + str(target[1])
            self.add_search_items(target[1], target, name, True)
            self.target_present = True
        else:
            self.target_present = False

        # 3.2) add the non-targets:
        self.num_lures = 0
        for non_target in non_targets:
            #print("NONTARGET ")
            #print(str(non_target))
            #                make_search_items(existing_list,num,color,shape,name = '',is_target=False)
            name = 'Lure=' + str(non_target[0]) + '_' + str(non_target[1])
            self.add_search_items(non_target[1], non_target, name, False)
            self.num_lures += non_target[1]
        #print("DISTRACTOR # " + str(self.num_lures))
        #print("NUM SEARCH ITEMS " + str(len(self.search_items)))
        # (2 alternate, 10/23) Set relevance on a dimension-by-dimension (not dimension class) basis
        # A dimension is relevant iff it distinguishes the target from any distractors
        # This is ONLY used for the parallel component of the search.
        # Things that are relevant are things that distinguish the target from the distractors
        self.relevant = []
        self.irrelevant = []
        # irrelevants are properties that are present in the stimuli but are constant across the target and distractors

        #for template_feature_list_index in range(len(self.search_template.feature_lists)):
        #    print("DEBUG " + str(template_feature_list_index))




        # new plan
        # iterate through all features in the outermost loop
        # 08/03/2023 RFH I think relevance should only be computed over non relation dimensions
        #for feature_index in range(len(self.search_template.feature_lists[0])):
        for feature_index in range(len(self.non_relation_dimensions)):
            is_relevant = False
            # print("VERIF non_relation_dimensions: " + str(self.non_relation_dimensions))
            #for this feature check to see whether it's relevant (different across the template and the search items )
            '''
            for template_list in self.search_template.feature_lists:
              
                for search_item in self.search_items:
                    for item_list in search_item.feature_lists:
                        # If the value of template_list[i] is not equal to the item_list[i] then i is relevant
                        if item_list[feature_index] != template_list[feature_index]:
                            is_relevant = True
                            
                            
            if is_relevant:
                self.relevant.append(feature_index)

            else:
                # If you make it his far (past the break) then i is the same in both the template list and item list
                # So i is not relevant. However, if it is present in either, then it's not absent but merely irrelevant
                is_irrelevant = False
                for feature_list in self.search_template.feature_lists:
                    if feature_list[feature_index] != 0: is_irrelevant = True
                if is_irrelevant: self.irrelevant.append(feature_index)
            '''
           
            for i in range(len(self.search_template.feature_lists)):
                for search_item in self.search_items:
                    if self.search_template.feature_lists[i][feature_index] != search_item.feature_lists[i][feature_index]:
                        is_relevant = True

            if is_relevant:
                self.relevant.append(feature_index)

            else:
                is_irrelevant = False
                for feature_list in self.search_template.feature_lists:
                    if feature_list[feature_index] != 0: is_irrelevant = True
                if is_irrelevant: self.irrelevant.append(feature_index)

        #print(self.relevant)
        #print(self.irrelevant)


        # DIAG
        print("* * * * * Here's your list of relevant dimensions: "+str(self.relevant))
        print("* * * * * Here's your list of irrelevant dimensions: " + str(self.irrelevant))
        # if len(self.search_items) > 1: exit()

        # 4) compute the vector lengths of the target template and the search items
        # get_vector_length(self,relevant,relevant_weight,irrelevant_weight)
        # 4.1) the search template
        #self.search_template.get_vector_length(self.relevant,self.RELEVANT_WEIGHT,self.IRRELEVANT_WEIGHT)

        # 4.2) the search items
        #for item in self.search_items:
        #    item.get_vector_length(self.relevant,self.RELEVANT_WEIGHT,self.IRRELEVANT_WEIGHT)


    # * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
    # * * * * * * * * * * Ancillary Functions * * * * * * * * * * *
    # * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *

    def item_comparison(self):
        """
        compares the feature vectors of all search items to the target template
         :return: 
        """
        # prepare to show the relevant dimensions
        relevant_list = []
        for i in range(len(self.search_template.features)):
            if i in self.relevant:
                relevant_list.append(1)
            else:
                relevant_list.append(0)
        #print( 'Relevant dimensions: '+str(relevant_list))
        #print( 'The target is:       '+str(self.search_template.features))
        #print( 'Similarity of Target to...')
        for item in self.search_items:
            similarity = self.feature_similarity(item.features)
            print( item.name+'         ('+str(item.features)+'): %.3f'%similarity)

    def clear_messages(self):
        # siimply inits the warnings list
        self.messages = []

    def make_message(self,text):
        # adds a warning to the list
        full_text = 'Iteration '+str(self.iteration)+') '+text
        self.messages.append(full_text)