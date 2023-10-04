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
# Developed and written by Rachel F Heaton and John E Hummel
# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *



import sys, SearchModel1, GraphicalRun1, copy, csv


# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
# * * * * * * * * * * The User Interface * * * * * * * * * * * *
# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *

class SearchModelInterface(object):
    """
    The graphical and text interface for the Attention Model
    """

    def __init__(self, the_model):
        self.model = the_model
        self.VERBOSE = False
        self.graphics_handler = None # this will be for graphical simulations
        self.graphics_failed  = GraphicalRun1.GRAPHICS_FAILED # you tried and failed to init the graphics

        # DIAG
        if self.graphics_failed:
            print( 'Pygame failed to load')
        else:
            print( 'Pygame loaded')


        self.wait = True  # wait for user to keypress between iterations

        self.message_list = [] # a list of strings to temm the interface what (if anything) has happened

        self.data_file_index = 0
        self.read_file_index()

        # data analysis stuff
        self.rt_summary_data          = [] # rts all runs over a condition
        self.suite_summary_rts        = []
        self.regression_summary_rts   = []
        self.selection_summary_data   = [] # num. attentional selections per run in a condition
        self.eye_move_summary_data    = [] # num eye movements per run per uondition
        self.auto_reject_summary_data = [] # num auto-rejected items per run by condition

    def read_file_index(self):
        """
        just reads the datafile index from the text file data_index.txt and sets self.data_file_index to it
        self.data_file_index is used to asign a unique index to each data file name so that they don't overwrite one another
        :return: 
        """
        index_file = open('data/data_index.txt','r')
        self.data_file_index = int(next(index_file)) # read the one and only line in the file, and cast it as an int (don't increment it yet; do that at time of file writing)
        index_file.close()

    def write_file_index(self):
        """
        just reads the datafile index from the text file data_index.txt and sets self.data_file_index to it
        self.data_file_index is used to asign a unique index to each data file name so that they don't overwrite one another
        :return: 
        """
        index_file = open('data/data_index.txt','w')
        index_file.write(str(self.data_file_index)) # write the index to the file
        index_file.close()

    def show_messages(self):
        # get any mesages form the attention model and show them immediately
        for message in self.model.messages:
            print( message)

    def show_data_structures(self):
        print( "\nAnd here's how the data structures stand at the end of the run...")
        all_items      = []
        viable_items   = []
        rejected_items = []
        for item in self.model.search_items:
            all_items.append(item.index)
        for item in self.model.viable_items:
            viable_items.append(item.index)
        for item in self.model.rejected_items:
            rejected_items.append(item.index)
        print( 'All search items: '+str(all_items))
        print( 'Viable items:     '+str(viable_items))
        print( 'Rejected items:   '+str(rejected_items))

    def run_blind(self, verbose_title=''):
        """
        runs the model with no graphics
        if self.Verbose, the it prints the self.model.event_list
        :return: 
        """
        self.model.run_whole_search(verbose_title)
        if self.VERBOSE:
            self.show_messages()

    def run_graphic(self, verbose_title=''):
        """
        attempt to run in graphic mode. if fail, then run blind
        :return: 
        """
        # ask whether user wants graphic run
        legal_responses = ('y', 'n')
        response = ''
        while not response in legal_responses:
            response = input('Graphic: (y)es or (n)o?')

        # if user wants blind run, then run blind
        if response == 'n':
            self.run_blind(verbose_title)

        # otherwise TRY to run graphic, and note whether you failed
        else:
            # if you don't already have the graphics handler, then try to create it
            if not self.graphics_handler:
                try:
                    self.graphics_handler = GraphicalRun1.GraphicalRun(self)
                except:
                    self.graphics_handler = None
                    self.graphics_failed  = True

            # if you have the graphics handler now, then run graphically
            if self.graphics_handler and not self.graphics_failed:
                self.graphics_handler.run(verbose_title)
            # otherwise, inform the user and just run blind
            else:
                print( "No go, Jack. I couldn't init the graphics handler.")
                self.run_blind(verbose_title)


    def run_suite(self, target, distractors, search_type, condition, num_distractors_list, num_runs, sim_id=None):
        """
        runs a suite of num_runs  simulations, blind and not verbose
        varies target present & absent, and num distractors
        collects the data, analyzes them and saves them to summary_data

        :param target is a list ['color','shape']
        :param distractors is a list of lists: [['color','shape'],['color','shape']]
        :param search_type is text: 'feature' or 'conjunction'
        :return: 
        """
        csv_file_name = str(search_type)  + '.csv'
        csv_data_file = open('data/' + csv_file_name, 'a', encoding='UTF8')
        writer=csv.writer(csv_data_file, delimiter =',')
        #writer.writerow(['resp.corr','total_setsize','trial_type','resp.rt','dcolor','participant'])
        self.suite_summary_rts = []
        #NUM_RUNS =  200 #Changed to argument to method 09/24/2019 RFH
        for num_targets in [1]: #"(1, 0):  # target absent [0] and present [1]
            # init all summary data

            self.rt_summary_data          = [] # mean rt per run by condition
            self.selection_summary_data   = [] # num. attentional selections per run in a condition
            self.eye_move_summary_data    = [] # num eye movements per run per condition
            self.auto_reject_summary_data = [] # num auto-rejected items per run by condition
            if num_targets == 1:
                target_type = 'present'
                file_name = search_type + '_pres.txt'
            else:
                target_type = 'absent'
                file_name = search_type + '_abs.txt'

            for num_distractors in num_distractors_list:
                # assemble the distractor list from the list (distractors) passed in
                if len(distractors) == 2:
                    num_dist_per = int(num_distractors / 2)  # half of the number of distractors for each distractor type
                else:
                    num_dist_per = num_distractors
                distractor_list = []

                for distractor in distractors:
                    # # print("DEBUG distractor: " + str(distractor))
                    this_dis_type = [distractor[0], num_dist_per]  # list is: [color,shape,number]
                    distractor_list.append(this_dis_type)


                # # print("DEBUG distractor_list in run_suite(): " + str(distractor_list))
                # create the simulation with the requisite targets and distractors:
                self.model.create_simulation([target[0],num_targets], distractor_list)
                # now run the simulations
                rt_data        = [] # rt on each run
                num_errors     = 0  # num errors over all runs
                selection_data = [] # num attentional selections per run
                eye_move_data  = [] # eye movements per run
                auto_rej_data  = [] # number of automatic rejections per run
                for i in range(num_runs):
                    self.model.run_whole_search()
                    if num_distractors == 0: recorded_condition = 0
                    else: recorded_condition = condition
                    participant = search_type.split('_')[0]
                    writer.writerow([str(int(self.model.correct)),str(num_distractors+1), 'expt', str(self.model.iteration),str(recorded_condition), participant])
                    if self.model.correct:  # count correct responses only
                        rt_data.append(self.model.iteration)
                        selection_data.append(self.model.num_attended)
                        eye_move_data.append(self.model.num_eye_movements)
                        auto_rej_data.append(self.model.num_auto_rejections)
                    else:
                        num_errors += 1
                        print("Errors " + str(num_errors))
                #print("RT DATA " + str(rt_data))
                if len(rt_data) > 0:
                    [rt_mean, rt_sem]  = self.mean_and_sem(rt_data)
                    [sel_mean,sel_sem] = self.mean_and_sem(selection_data)
                    [eye_mean,eye_sem] = self.mean_and_sem(eye_move_data)
                    [rej_mean,rej_sem] = self.mean_and_sem(auto_rej_data)
                else:
                    print( 'WOAH! All errors. Num errors = '+str(num_errors))
                    print( 'Condition: '+file_name)

                # RT data
                self.model.make_message(str(num_distractors) + ' lures, ' + search_type + ' search, target' + target_type + ', Mean RT (sem) = %.3f (%.3f), Errors = %2i' %(rt_mean,rt_sem,num_errors))
                self.rt_summary_data.append([self.model.num_lures, rt_mean, rt_sem, num_errors])

                # TODO Thsi is where the graph needs to be made and saved to disk


                # attentional selection summary data
                self.model.make_message('Mean Num. Attn. Sel. (sem) = %.3f (%.3f)' %(sel_mean, sel_sem))
                self.selection_summary_data.append([self.model.num_lures, sel_mean, sel_sem])

                # eye movement summary data
                self.model.make_message('Mean Num. Eye Movements (sem) = %.3f (%.3f)' % (eye_mean, eye_sem))
                self.eye_move_summary_data.append([self.model.num_lures, eye_mean, eye_sem])

                # auto-rejection summary data
                self.model.make_message('Mean Num. Auto Rejections (sem) = %.3f (%.3f)' % (rej_mean, rej_sem))
                self.auto_reject_summary_data.append([self.model.num_lures, rej_mean, rej_sem])

            #graph_rt_summary_data = copy.deepcopy(self.rt_summary_data)

                type= 'Target ' + str(target) + ', Distractors' + str(distractors)
            graph_rt_summary_data = [type, copy.deepcopy(self.rt_summary_data)]


            self.suite_summary_rts.append(graph_rt_summary_data)
            # * * * * * save the data to file: * * * * *

            #   1) DON't increment the data file index: bad to do this here: creates a separate index for each of the four simulations run in a suite. do it when the suite is defined
            #    self.data_file_index += 1
            #   2) format the index as a string with three digits (only up to 999 unique filenames)
            index_string = '(%3i)'%self.data_file_index
            #   3) append the index to the beginning of the file
            file_name = index_string+'_'+str(condition)+'_'+file_name
            data_file = open('data/'+file_name, 'w')

            # RT and error data
            data_file.write(str(num_runs)+' runs of SearchModel1 (last modified '+str(self.model.LAST_MODIFIED)+')\n\n')
            data_file.write(search_type+' search\n')
            data_file.write('Target '+target_type+'\n\n') # target_type = 'present' or 'absent'
            data_file.write('Target: '+str(target)+'\n')
            data_file.write('Distractors: '+str(distractors)+'\n\n\n')
            data_file.write('RT and accuracy (n = num. distractors; rt = mean rt; sem = std. error of mean; err = num errors):\n')
            data_file.write('n\trt\t\tsem\t\terr\n')
            for line in self.rt_summary_data:
                text_data = [str(line[0])]  # line[0] is the number of lures: an integer
                text_data.append('%.3f' % line[1])  # line[1] is the mean RT
                text_data.append('%.3f' % line[2])  # line[2] is the sem
                text_data.append(str(line[3]))      # line[3] is the number of errors
                text_data.append('\n')
                text_line = '\t'.join(text_data)
                data_file.write(text_line)

            # compute and report the slope & intercept of the regression line, and
            #   the variance accounted for  y the linear trend
            #(slope, intercept, variance_accounted) = self.slope_and_intercept(self.rt_summary_data)
            #data_file.write('\n')
            #data_file.write('Slope      = %.3f iterations/item\n'%slope)
            #data_file.write('Intercept  = %.3f iterations\n'%intercept)
            #data_file.write('Percent Variance Accounted for = %.3f\n'%(100*variance_accounted))

            # attentional selection data
            data_file.write('\n\nAttentional Selection Data (n = num. distractors; s = mean selections; sem = std. error of mean):\n')
            data_file.write('n\ts\t\tsem\n')
            for line in self.selection_summary_data:
                text_data = [str(line[0])]  # line[0] is the number of lures: an integer
                text_data.append('%.3f' % line[1])  # line[1] is the mean RT
                text_data.append('%.3f' % line[2])  # line[2] is the sem
                text_data.append('\n')
                text_line = '\t'.join(text_data)
                data_file.write(text_line)

            # eye movement data
            data_file.write(
                '\n\nEye Movement Data (n = num. distractors; em = mean eye movements; sem = std. error of mean):\n')
            data_file.write('n\tem\t\tsem\n')
            for line in self.eye_move_summary_data:
                text_data = [str(line[0])]  # line[0] is the number of lures: an integer
                text_data.append('%.3f' % line[1])  # line[1] is the mean RT
                text_data.append('%.3f' % line[2])  # line[2] is the sem
                text_data.append('\n')
                text_line = '\t'.join(text_data)
                data_file.write(text_line)

            # automatic rejection data (lure rejections w/o attention)
            data_file.write(
                '\n\nAutomatic Lure Rejection Data (n = num. distractors; nr = mean num. auto rejections; sem = std. error of mean):\n')
            data_file.write('n\tnr\t\tsem\n')
            for line in self.auto_reject_summary_data:
                text_data = [str(line[0])]  # line[0] is the number of lures: an integer
                text_data.append('%.3f' % line[1])  # line[1] is the mean RT
                text_data.append('%.3f' % line[2])  # line[2] is the sem
                text_data.append('\n')
                text_line = '\t'.join(text_data)
                data_file.write(text_line)

            # write the parameter values to the file
            self.write_parameters(data_file)

            # finally, close the data file
            data_file.close()

            print( file_name+' saved to Data/')
        print(self.suite_summary_rts)
        csv_data_file.close()
        self.regression_summary_rts.append(self.suite_summary_rts)

    # * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
    # * * * * * * * * * * Data handling * * * * * * * * * * *
    # * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *

    def mean_and_sem(self, data):
        # compute the mean and std. error of mean (sem) of the data
        mean = 0.0
        # get mean & n
        n = len(data)
        if n > 0:
            for datum in data:
                mean += datum
            mean /= n
            # compute sd
            sd = 0.0
            for datum in data:
                sd += pow(datum - mean, 2)
            sd = pow(sd, 0.5)
            sem = sd / pow(n, 0.5)
            return (mean, sem)
        else:
            return None

    def slope_and_intercept(self,data):
        """
        computes the slope and intercept of the search function
        :param data: [num,rt,sem,num_errors]
        :return:
        """
        N  = 0 # the index into data of the N's
        RT = 1 # the index of the data into the RT's

        # 1) first get the correlation between data[0] (n) and data[1] (rt)
        means      = [0.0,0.0]# mean of n and rt
        variances  = [0.0,0.0]
        # 1.1) get the of the n and rt data
        num_scores = 0 # number of rts and ns
        for entry in data: # for each entry
            means[N]   += entry[N]
            means[RT]  += entry[RT]
            num_scores += 1
        means[N]  /= num_scores
        means[RT] /= num_scores
        # 1.2) get the variances
        for entry in data:
            variances[N]  += (means[N]  - entry[N])  ** 2
            variances[RT] += (means[RT] - entry[RT]) ** 2
        variances[N]  = pow(variances[N],  0.5)
        variances[RT] = pow(variances[RT], 0.5)
        # 1.3) numerator of correlation
        numerator = 0.0
        for i in range(len(data)):
            numerator += (data[i][N] - means[N]) * (data[i][RT] - means[RT])
        # 1.4) denominator for correlation
        Ns_length  = 0.0
        RTs_length = 0.0
        for i in range(len(data)):
            Ns_length  += (data[i][N]  - means[N])** 2
            RTs_length += (data[i][RT] - means[RT])** 2
        Ns_length  = pow(Ns_length,0.5)
        RTs_length = pow(RTs_length,0.5)
        # 1.5) the correlation & variance accounted for
        correlation = numerator/(Ns_length * RTs_length)
        variance_accounted = correlation**2

        # 2) slope = correlation * rise/run = correlation * (RT_variance/N_varniance)
        slope = correlation * variances[RT]/variances[N]

        # 3) intercept
        # y = mx + b, where y = mean RT and x = mean N and m = slope
        # b = y - mx
        intercept = means[RT] - slope * means[N]

        return (slope, intercept, variance_accounted)

    # * * * * * * * * * * * * * * * * * * * * * * * *
    # * * * * * * * * * * Menus * * * * * * * * * * *
    # * * * * * * * * * * * * * * * * * * * * * * * *

    def write_parameter_description(self,number):
        """
        given a parameter number, read and display the text file explaining the parameter
        :param number: 
        :return: 
        """
        # 2/14/19: figure out whether option 7 is DISTANCE_FALLOFF_RATE (if not LINEAR_DISTANCE_COST) or DISTANCE_AT_ZERO (if LINEAR_DISTANCE_COST)
        if number == 8 and self.model.LINEAR_DISTANCE_COST:
            # if they're asking about DISTANCE_FALLOFF_RATE when the cost is linear, then...
            number = 19 # ... they're really asking about DISTANCE_AT_ZERO

        parameter_names = {1:'TARGET_MATCH_THRESHOLD',
                           2:'REJECTION_THRESHOLD',
                           3:'TARGET_ABSENT_COST',
                           4:'P_RELEVANT_SAMPLING',
                           5:'P_IRRELEVANT_SAMPLING',
                           6:'MIN_SELECTION_PRIORITY',
                           7:'LINEAR_DISTANCE_COST',
                           8:'DISTANCE_FALLOFF_RATE',
                           9:'RELEVANT_WEIGHT',
                           10:'IRRELEVANT_WEIGHT',
                           11:'COSINE_THRESHOLD',
                           12:'ATTENTION_SHIFT_COST',
                           13:'EYE_MOVEMENT_TIME_COST',
                           14:'INTEGRATOR_GUIDED_PRIORITY',
                           15:'PERMIT_EYE_MOVEMENTS',
                           16:'ITEM_RADIUS',
                           17:'ITEM_DISTANCE',
                           18:'CARTESIAN_GRID',
                           19:'DISTANCE_AT_ZERO'}
        try:
            file_name = 'helpfiles/'+parameter_names[number]+'.txt'
        except:
            print( str(number)+' is an invalid key into parameter_names')
            return 0

        # if you get this far, then open the file and print( its contents)
        info_file = open(file_name,'r')
        all_done = False
        print
        print
        while not(all_done):
            try:
                text_line = info_file.next() # get next line
                text_line = text_line.rstrip('\n')
                print( text_line)
            except StopIteration or EOFError:  # StopIteration is the exception thrown by file.next() when EOF encountered
                info_file.close()
                all_done = True
                print

    def write_parameters(self,data_file=None):
        """
        write parameters, either to screen (graphic or not) or to file
        :param file: if None, then write to screen
        :return:
        """
        text_lines = []

        text_lines.append('\n* * * Parameter Values * * *')
        text_lines.append('\nSearch item rejection and acceptance parameters:')
        #text_lines.append('(1)  TARGET_MATCH_THRESHOLD    = %.2f' % self.model.TARGET_MATCH_THRESHOLD)
        text_lines.append('(2)  REJECTION_THRESHOLD       = %.2f' % self.model.REJECTION_THRESHOLD)
        text_lines.append('(3)  TARGET_ABSENT_COST        = ' + str(self.model.TARGET_ABSENT_COST))
        text_lines.append('\nRandom sampling during inattention:')
        text_lines.append('(4)  P_RELEVANT_SAMPLING       = %.3f' % self.model.P_RELEVANT_SAMPLING)
        text_lines.append('(5)  P_IRRELEVANT_SAMPLING     = %.3f' % self.model.P_IRRELEVANT_SAMPLING)
        text_lines.append('(6)  MIN_SELECTION_PRIORITY    = %.3f' % self.model.MIN_SELECTION_PRIORITY)
        text_lines.append('\nEffect of distance between fixation and item location in the display:')
        text_lines.append('(7)  LINEAR_DISTANCE_COST      = ' +str(self.model.LINEAR_DISTANCE_COST))
        if self.model.LINEAR_DISTANCE_COST:
            text_lines.append('(8)  DISTANCE_AT_ZERO          = ' + str(self.model.DISTANCE_AT_ZERO))
        else:
            text_lines.append('(8)  DISTANCE_FALLOFF_RATE     = %.3f' % self.model.DISTANCE_FALLOFF_RATE)
        text_lines.append('\nFeature weighting under selected processing:')
        #text_lines.append('(9)  RELEVANT_WEIGHT           = %.3f' % self.model.RELEVANT_WEIGHT)
        #text_lines.append('(10) IRRELEVANT_WEIGHT         = %.3f' % self.model.IRRELEVANT_WEIGHT)
        #text_lines.append('(11) COSINE_THRESHOLD          = %.3f' % self.model.COSINE_THRESHOLD)
        text_lines.append('\nOperation cost parameters:')
        text_lines.append('(12) ATTENTION_SHIFT_COST      = ' + str(self.model.ATTENTION_SHIFT_COST))
        text_lines.append('(13) EYE_MOVEMENT_TIME_COST    = ' + str(self.model.EYE_MOVEMENT_TIME_COST))
        text_lines.append('\nSearch behavior parameters:')
        #text_lines.append('(14) INTEGRATOR_GUIDED_PRIORITY = %.3f' % self.model.INTEGRATOR_GUIDED_PRIORITY)
        text_lines.append('(15) PERMIT_EYE_MOVEMENTS       = ' + str(self.model.PERMIT_EYE_MOVEMENTS))
        text_lines.append('\nDisplay characteristics:')
        text_lines.append('(16) ITEM_RADIUS                = ' + str(self.model.ITEM_RADIUS))
        text_lines.append('(17) ITEM_DISTANCE              = ' + str(self.model.ITEM_DISTANCE))
        text_lines.append('(18) CARTESIAN_GRID             = ' + str(self.model.CARTESIAN_GRID))

        if data_file:
            # if writing to data file, write the model's last modified date as well as the parameters
            data_file.write('\n\nModel Last Modified '+self.model.LAST_MODIFIED+'\n\n')
            for line in text_lines:
                line = line + '\n' # add carriage returns at the ends for the file; not needed for print( below)
                data_file.write(line)
        else:
            # if writing to screen, then just return the lines to write
            return text_lines

    def run_premade_simulation(self):
        self.VERBOSE = True

        print
        print( 'Pre-made searches are for a red vertical among...')
        print( 'green verticals in the case of feature search or')
        print( 'green verticals and red horizontals in the case of conjunction search.')

        # get search type
        print
        print( 'Which do you want?')
        search_types = ('f','c','a')
        search_type = ''
        while not search_type in search_types:
            search_type = input('(f)eature, (c)onjunction or (a)bort search?')
        if search_type == 'a':
            return 0

        # get target present/absent
        target_types = ('p', 'a')
        target_type = ''
        while not target_type in target_types:
            target_type = input('Target (p)resent or (a)bsent?')

        # get num distractors
        print( 'And how many distractors? (Choose an even number for conjunction search.)')
        num_distractors = ''
        while not type(num_distractors) == int:
            numinput = input('gimme an int >')
            num_distractors = int(numinput)

        # if you got to this point, then you're good
        if target_type == 'p':
            target = [[['red','vertical', 'none']],1]
        else:
            target = [[['red','vertical', 'none']],0]
        if search_type == 'f':
            distractors = [[[['green', 'vertical', 'none']], num_distractors]]
        else:
            distractors = [[[['green', 'vertical', 'none']], int(num_distractors/2)],[[['red', 'horizontal','none']], int(num_distractors/2)]]

        # create the search
        self.model.create_simulation(target, distractors)

        # and run it
        if search_type == 'f': search_text = 'Feature'
        elif search_type == 'c' : search_text = 'Conjunction'
        else: search_text = 'Relation'
        if target_type == 'p': target_text = 'Present'
        else: target_text = 'Absent'

        # if you already know the graphics don't work, then just run blind
        if self.graphics_failed:
            self.run_blind('\n\n'+search_text+' Search, Target '+target_text)
        # otherwise, ask the user whether s/he wants to run graphic
        else:
            self.run_graphic('\n\n'+search_text+' Search, Target '+target_text) #run_graphic only Asks about -- and maybe tried -- a graphic run

        return 1

    def run_handmade_simulation(self):
        """
        like run_premade_simulation except that the user enters the search target & distractors
        :return:
        """
        self.VERBOSE = True

        print
        print( '* * * Design a Simulation * * *')
        print
        print( 'Step 1: Make the target')
        target = []
        # get the properties of part 1
        print('Step 1.1: make the first (and perhaps only) part of the target')
        print("The legal colors are: "+str(self.model.legal_colors))
        target_color = ''
        while not (target_color in self.model.legal_colors):
            target_color = input('Part color >')
        print( 'the legal shapes are: '+str(self.model.legal_shapes))
        target_shape = ''
        while not (target_shape in self.model.legal_shapes):
            target_shape = input('Part shape >')
        print("The legal relations are: " + str(self.model.legal_roles) +" (use 'none' for a one-part target)")
        target_role = 'bullshit'
        other_role  = 'none'
        while not (target_role in self.model.legal_roles):
            target_role = input('Part relation>')
            if target_role == 'above': other_role = 'below'
            elif target_role == 'below': other_role = 'above'
            else: other_role = 'none'
        # at this point, you have everything you need to make one (and perhaps the only) parta

        #target_properties = [[target_color,target_shape,target_role]]
        target_properties = [[target_color, target_shape, target_role]]
        # if the role of the first part is not 'none' then make a second part with the complementary relational role
        if other_role != 'none':
            print('Step 1.2: make the part of the target that is '+other_role+' the first one.')
            print("The legal colors are: "+str(self.model.legal_colors))
            target_color = input('Part color >')
            print( 'the legal shapes are: '+str(self.model.legal_shapes))
            target_shape = input('Part shape >')
            target_properties.append([target_color,target_shape,other_role])

        print( 'How many targets: 1 (target present) or 0 (target absent)')
        target_number = 10
        while not target_number in (0,1):
            target_number = int(input('Target number (0 or 1) >'))

        target = [target_properties, target_number]
        print
        print("Here's your target: "+str(target))
        print

        print('Step 2: Make some distractors/lures (same constraints as for targets)')
        done_with_lures = False
        distractors = []
        while not done_with_lures:
            lure_color = ''
            while not (lure_color in self.model.legal_colors):
                lure_color = input('Lure color >')
            lure_shape = ''
            while not (lure_shape in self.model.legal_shapes):
                lure_shape = input('Lure shape>')
            lure_relation = ''
            while not(lure_relation in self.model.legal_roles):
                lure_relation = input('Lure relation >')
                if lure_relation == 'none': other_role = 'none'
                elif lure_relation == 'above': other_role = 'below'
                elif lure_relation == 'below': other_role = 'above'
                else: print('In the words of David Byrne, "How did I get here??"')
            lure_properties = [[lure_color,lure_shape,lure_relation]]
            if other_role != 'none':
                # get the feature of this item's other part
                lure_color = ''
                while not (lure_color in self.model.legal_colors):
                    lure_color = input('Lure color >')
                lure_shape = ''
                while not (lure_shape in self.model.legal_shapes):
                    lure_shape = input('Lure shape>')
                lure_properties.append([lure_color,lure_shape,other_role])
            lure_number = int(input('How many '+str(lure_properties)+'s? >'))
            distractors.append([lure_properties, lure_number])
            print( 'Your lures so far: '+str(distractors))
            legal_responses = ('y','n')
            response = ''
            while not response in legal_responses:
                response = input('Make another lure (y/n)? >')
                if response == 'n':
                    done_with_lures = True

        # create the search
        self.model.create_simulation(target, distractors)

        # and run it

        #TODO: FIX THIS THIS IS SO WRONG
        # MAke sure target differs on the right dimensions
        if len(distractors) == 1: search_text = 'Feature'
        else: search_text = 'Conjunction'
        if target[1] == 1: target_text = 'Present'
        else: target_text = 'Absent'


        # if you already know the graphics don't work, then just run blind
        if self.graphics_failed:
            self.run_blind('\n\n'+search_text+' Search, Target '+target_text)
        # otherwise, ask the user whether s/he wants to run graphic
        else:
            self.run_graphic('\n\n'+search_text+' Search, Target '+target_text) #run_graphic only Asks about -- and maybe tried -- a graphic run

        return 1

    def run_handmade_suite(self):
        """
        like run_premade_suite except that the user enters the search target & distractors
        Added 09/24/2019 RFH
        :return:
        """
        self.regression_summary_rts = []
        #TODO: add ability to run more than one suite
        self.VERBOSE = True

        print
        print( '* * * Design a Simulation (Suite) * * *')
        print
        print('Step 1: Make the target')
        target = []
        # get the properties of part 1
        print('Step 1.1: make the first (and perhaps only) part of the target')
        print("The legal colors are: " + str(self.model.legal_colors))
        target_color = ''
        while not (target_color in self.model.legal_colors):
            target_color = input('Part color >')
        print('the legal shapes are: ' + str(self.model.legal_shapes))
        target_shape = ''
        while not (target_shape in self.model.legal_shapes):
            target_shape = input('Part shape >')
        print("The legal relations are: " + str(self.model.legal_roles) + " (use 'none' for a one-part target)")
        target_role = 'bullshit'
        other_role = 'none'
        while not (target_role in self.model.legal_roles):
            target_role = input('Part relation>')
            if target_role == 'above':
                other_role = 'below'
            elif target_role == 'below':
                other_role = 'above'
            else:
                other_role = 'none'
        # at this point, you have everything you need to make one (and perhaps the only) parta

        # target_properties = [[target_color,target_shape,target_role]]
        target_properties = [[target_color, target_shape, target_role]]
        # if the role of the first part is not 'none' then make a second part with the complementary relational role
        if other_role != 'none':
            print('Step 1.2: make the part of the target that is ' + other_role + ' the first one.')
            print("The legal colors are: " + str(self.model.legal_colors))
            target_color = input('Part color >')
            print('the legal shapes are: ' + str(self.model.legal_shapes))
            target_shape = input('Part shape >')
            target_properties.append([target_color, target_shape, other_role])

        print('How many targets: 1 (target present) or 0 (target absent)')
        target_number = 10
        while not target_number in (0, 1):
            target_number = int(input('Target number (0 or 1) >'))

        target = [target_properties, target_number]
        print
        print("Here's your target: " + str(target))
        print

        print('Step 2: Make some distractors/lures (same constraints as for targets)')
        done_with_lures = False
        distractors = []
        while not done_with_lures:
            lure_color = ''
            while not (lure_color in self.model.legal_colors):
                lure_color = input('Lure color >')
            lure_shape = ''
            while not (lure_shape in self.model.legal_shapes):
                lure_shape = input('Lure shape>')
            lure_relation = ''
            while not (lure_relation in self.model.legal_roles):
                lure_relation = input('Lure relation >')
                if lure_relation == 'none':
                    other_role = 'none'
                elif lure_relation == 'above':
                    other_role = 'below'
                elif lure_relation == 'below':
                    other_role = 'above'
                else:
                    print('In the words of David Byrne, "How did I get here??"')
            lure_properties = [[lure_color, lure_shape, lure_relation]]
            if other_role != 'none':
                # get the feature of this item's other part
                lure_color = ''
                while not (lure_color in self.model.legal_colors):
                    lure_color = input('Lure color >')
                lure_shape = ''
                while not (lure_shape in self.model.legal_shapes):
                    lure_shape = input('Lure shape>')
                lure_properties.append([lure_color, lure_shape, other_role])
            lure_number = int(input('How many ' + str(lure_properties) + 's? >'))
            distractors.append([lure_properties, lure_number])
            print('Your lures so far: ' + str(distractors))
            legal_responses = ('y', 'n')
            response = ''
            while not response in legal_responses:
                response = input('Make another lure (y/n)? >')
                if response == 'n':
                    done_with_lures = True
        done_with_num_distractors = False

        num_distractor_list = [2, 4, 8, 16, 32, 64]



        num_runs = input('Number of simulations >')
        num_runs = int(num_runs)

        #TODO This is wrong in the same way as the run handmade simulation is wrong. See above.
        if len(distractors) == 1: search_text = 'Feature'
        else: search_text = 'Conjunction'

        self.run_suite(target, distractors, search_text, 1 , num_distractor_list, num_runs)

        self.graph_regression()
        return 1



    def run_premade_suite(self):
        """
        run a suite of simulations: red vertical among...
        runs feature & conjunction searches, target present and absent,
        many numbers of distractors, and saves the results to data files
        :return:
        """
        self.model.VERBOSE = False

        print("Which premade simulation would you like to run?")
        print(" 1 - Simulation 1: Treisman & Gelade (1980)\n")
        print(" 2 - Simulation 2: Wolfe et al. (1989)\n")
        print(" 3 - Simulation 3: Buetti et al. (2016)\n")
        print(" 4 - Simulation 4: Treisman & Souther (1985)\n")
        print(" 5 - Simulation 5: Pomerantz et al. (1977)\n")
        print(" 6 - Simulation 6: Similar to Logan (1994) using multicolor items\n")
        print(" 7 - Simulation 7: Similar to Logan (1994) using single color items\n")
        print(" 8 - Simulation 8: Multicolor relations with emergent feature, default salience\n")
        print(" 9 - Simulation 8: Multicolor relations with emergent feature, reduced salience\n")
        print("10 - Simulation 9: Monocolor relations with emergent feature, default salience\n")
        print("11 - Simulation 9: Monocolor relations with emergent feature in relation-only condition only\n")
        print("12 - Simulation 10: Multicolor relations with emergent feature with increased spacing\n")

        SIM_ID = 99
        while not (SIM_ID in {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12}):
            SIM_ID = int(input('Simulation number >'))


        # increment the datafile index here: should be a unique index for each SUITE of simulations run
        self.data_file_index += 1
        self.regression_summary_rts = []


        if SIM_ID == 1:
        # # # 1) Triesman & Gelade (1980)

            dim_index = 0
            for i in range(len(self.model.color_vectors['red'])):
                self.model.COLOR_DIMENSIONS.append(dim_index)
                dim_index += 1

            for i in range(len(self.model.shape_vectors['X'])):
                self.model.SHAPE_DIMENSIONS.append(dim_index)
                dim_index += 1

            for i in range(len(self.model.relation_vectors['above'])):
                self.model.RELATION_DIMENSIONS.append(dim_index)
                dim_index += 1

            self.model.non_relation_dimensions = self.model.COLOR_DIMENSIONS + self.model.SHAPE_DIMENSIONS
            self.model.salience = [1] * 18 + [1] * 27


            num_subjects = 100
            for subject in range(num_subjects):
                csv_file_name = str(self.data_file_index) + '.csv'
                csv_data_file = open('data/' + csv_file_name, 'a', encoding='UTF8')
                writer = csv.writer(csv_data_file, delimiter=',')
                writer.writerow(['resp.corr', 'total_setsize', 'trial_type', 'resp.rt', 'dcolor', 'participant'])
                csv_data_file.close()
                self.run_suite([[['blue', 'X', 'none']], 1], [[[['dkgrn', 'X','none']],1], [[['brown', 'T1','none']],1]], str(self.data_file_index), 1, [0, 4, 14, 29],52)
                self.run_suite([[['dkgrn', 'T1', 'none']], 1], [[[['dkgrn', 'X', 'none']], 1], [[['brown', 'T1', 'none']], 1]], str(self.data_file_index), 2, [0, 4, 14, 29], 52)

                self.data_file_index += 1

        elif SIM_ID == 2:
        # # # 2) Wolfe, Cave & Franzel (1989)

            dim_index = 0
            for i in range(len(self.model.color_vectors['red'])):
                self.model.COLOR_DIMENSIONS.append(dim_index)
                dim_index += 1

            for i in range(len(self.model.shape_vectors['X'])):
                self.model.SHAPE_DIMENSIONS.append(dim_index)
                dim_index += 1

            for i in range(len(self.model.relation_vectors['above'])):
                self.model.RELATION_DIMENSIONS.append(dim_index)
                dim_index += 1

            self.model.non_relation_dimensions = self.model.COLOR_DIMENSIONS + self.model.SHAPE_DIMENSIONS
            self.model.salience = [1] * 18 + [1] * 27

            num_subjects = 100
            for subject in range(num_subjects):
                csv_file_name = str(self.data_file_index) + '.csv'
                csv_data_file = open('data/' + csv_file_name, 'a', encoding='UTF8')
                writer = csv.writer(csv_data_file, delimiter=',')
                writer.writerow(['resp.corr', 'total_setsize', 'trial_type', 'resp.rt', 'dcolor', 'participant'])
                csv_data_file.close()
                self.run_suite([[['green', 'horizontal', 'none']], 1], [[[['red', 'vertical', 'none']], 1]], str(self.data_file_index), 1, [0, 2, 4, 8, 16, 24, 36], 52)
                self.run_suite([[['green', 'horizontal','none']],1], [[[['green', 'vertical','none']],1], [[['red', 'horizontal','none']],1]], str(self.data_file_index), 2, [0, 2, 4, 8, 16, 24, 36],52)
                self.data_file_index += 1

        elif SIM_ID == 3:
        # # # 3) Target-distractor similarity (Buetti et al., 2016)

            dim_index = 0
            for i in range(len(self.model.color_vectors['red'])):
                self.model.COLOR_DIMENSIONS.append(dim_index)
                dim_index += 1

            for i in range(len(self.model.shape_vectors['X'])):
                self.model.SHAPE_DIMENSIONS.append(dim_index)
                dim_index += 1

            for i in range(len(self.model.relation_vectors['above'])):
                self.model.RELATION_DIMENSIONS.append(dim_index)
                dim_index += 1

            self.model.non_relation_dimensions = self.model.COLOR_DIMENSIONS + self.model.SHAPE_DIMENSIONS
            self.model.salience = [1] * 18 + [1.5] * 27

            num_subjects = 100
            for subject in range(num_subjects):
                csv_file_name = str(self.data_file_index) + '.csv'
                csv_data_file = open('data/' + csv_file_name, 'a', encoding='UTF8')
                writer = csv.writer(csv_data_file, delimiter=',')
                writer.writerow(['resp.corr', 'total_setsize', 'trial_type', 'resp.rt', 'dcolor', 'participant'])
                csv_data_file.close()
                self.run_suite([[['red', 'vertical', 'none']], 1], [[[['ltblue', 'horizontal', 'none']], 1]], str(self.data_file_index), 1, [0, 1, 4, 9, 19, 31], 52)
                self.run_suite([[['red', 'vertical', 'none']], 1], [[[['yel2ow', 'vertical', 'none']], 1]], str(self.data_file_index), 2, [0, 1, 4, 9, 19, 31], 52)
                self.run_suite([[['red', 'vertical', 'none']], 1], [[[['orange', 'vertical', 'none']], 1]], str(self.data_file_index), 3, [0, 1, 4, 9, 19, 31], 52)
                self.data_file_index += 1


        elif SIM_ID == 4:
        # # # 4) Search asymmetries (Treisman & Souther, 1985)

            dim_index = 0
            for i in range(len(self.model.color_vectors['red'])):
                self.model.COLOR_DIMENSIONS.append(dim_index)
                dim_index += 1

            for i in range(len(self.model.shape_vectors['X'])):
                self.model.SHAPE_DIMENSIONS.append(dim_index)
                dim_index += 1

            for i in range(len(self.model.relation_vectors['above'])):
                self.model.RELATION_DIMENSIONS.append(dim_index)
                dim_index += 1

            self.model.non_relation_dimensions = self.model.COLOR_DIMENSIONS + self.model.SHAPE_DIMENSIONS
            self.model.salience = [1] * 18 + [1] * 27

            num_subjects = 100
            for subject in range(num_subjects):
                csv_file_name = str(self.data_file_index) + '.csv'
                csv_data_file = open('data/' + csv_file_name, 'a', encoding='UTF8')
                writer = csv.writer(csv_data_file, delimiter=',')
                writer.writerow(['resp.corr', 'total_setsize', 'trial_type', 'resp.rt', 'dcolor', 'participant'])
                csv_data_file.close()
                self.run_suite([[['white', 'Q', 'none']],1], [[[['white', 'O','none']],1]],  str(self.data_file_index), 1, [0,5,11], 100)
                self.run_suite([[['white', 'O','none']],1], [[[['white', 'Q','none']],1]], str(self.data_file_index), 2, [0,5,11], 100)
                self.data_file_index += 1

        elif SIM_ID == 5:
        # # # 5) Search for oppositely oriented diagonals and Pomerantz stimuli Pomerantz, Saeger, and Stover (1977)

            dim_index = 0
            for i in range(len(self.model.color_vectors['red'])):
                self.model.COLOR_DIMENSIONS.append(dim_index)
                dim_index += 1

            for i in range(len(self.model.shape_vectors['P1'])):
                self.model.SHAPE_DIMENSIONS.append(dim_index)
                dim_index += 1

            for i in range(len(self.model.relation_vectors['above'])):
                self.model.RELATION_DIMENSIONS.append(dim_index)
                dim_index += 1

            self.model.non_relation_dimensions = self.model.COLOR_DIMENSIONS + self.model.SHAPE_DIMENSIONS
            self.model.salience = [1] * 18 + [1] * 27 + [1] * self.model.POMERANTZ_UNITS + [1] * self.model.POMERANTZ_UNITS

            num_subjects = 64
            participant = self.data_file_index
            for subject in range(num_subjects):
                csv_file_name = str(self.data_file_index) + '.csv'
                search_type = str(self.data_file_index)
                csv_data_file = open('data/' + csv_file_name, 'a', encoding='UTF8')
                writer = csv.writer(csv_data_file, delimiter=',')
                writer.writerow(['resp.corr', 'total_setsize', 'trial_type', 'resp.rt', 'dcolor', 'participant'])
                csv_data_file.close()
                self.run_suite([[['red', 'DORN2','none']],1], [[[['red', 'DORN6','none']],1]], search_type, 1, [1, 3, 5], 100)
                self.run_suite([[['red', 'P1','none']],1], [[[['red', 'P2','none']],1]], search_type, 2, [1, 3, 5], 100)
                self.run_suite([[['red', 'arrow','none']],1], [[[['red', 'triangle','none']],1]], search_type, 3, [1, 3, 5], 100)
                self.data_file_index += 1
        # '''
        # self.data_file_index -= num_subjects
        # for subject in range(num_subjects):
        #     csv_file_name = str(self.data_file_index) +  '_2.csv'
        #     search_type = str(self.data_file_index) + '_2'
        #     csv_data_file = open('data/' + csv_file_name, 'a', encoding='UTF8')
        #     writer = csv.writer(csv_data_file, delimiter=',')
        #     writer.writerow(['resp.corr', 'total_setsize', 'trial_type', 'resp.rt', 'dcolor', 'participant'])
        #     csv_data_file.close()
        #     #self.run_suite([[['red', 'DORN2','none']],1], [[[['red', 'DORN6','none']],1]], str(self.data_file_index), 1, [0, 1, 3, 5], 100)
        #     self.run_suite([[['red', 'P1','none']],1], [[[['red', 'P2','none']],1]], search_type, 2, [0, 1, 3, 5], 100)
        #     self.data_file_index += 1


        #
        # # # # 5) Relational Searches
        #No cheat feature multicolor
        elif SIM_ID == 6:

            dim_index = 0
            for i in range(len(self.model.color_vectors['red'])):
                self.model.COLOR_DIMENSIONS.append(dim_index)
                dim_index += 1

            for i in range(len(self.model.shape_vectors['cheatXabove'])):
                self.model.SHAPE_DIMENSIONS.append(dim_index)
                dim_index += 1

            for i in range(len(self.model.relation_vectors['above'])):
                self.model.RELATION_DIMENSIONS.append(dim_index)
                dim_index += 1

            self.model.non_relation_dimensions = self.model.COLOR_DIMENSIONS + self.model.SHAPE_DIMENSIONS
            self.model.salience = [1] * 18 + [1] * 27 + [1]*2

            num_subjects = 32
            for subject in range(num_subjects):
                csv_file_name = str(self.data_file_index) + '.csv'
                csv_data_file = open('data/' + csv_file_name, 'a', encoding='UTF8')
                writer = csv.writer(csv_data_file, delimiter=',')
                writer.writerow(['resp.corr', 'total_setsize', 'trial_type', 'resp.rt', 'dcolor', 'participant'])
                csv_data_file.close()
                self.run_suite([[['red', 'nocheatX', 'above'], ['green', 'nocheatO', 'below']], 1], [[[['green','nocheatO', 'above'],['red', 'nocheatX', 'below']], 1]], str(self.data_file_index), 1, [0, 1, 3, 7, 15], 52)#[0, 1, 3, 7, 15], 52)
                self.run_suite([[['red', 'nocheatX', 'above'], ['green', 'nocheatO', 'below']], 1], [[[['green', 'nocheatO', 'above'], ['orange', 'nocheatX', 'below']], 1]], str(self.data_file_index), 2, [0, 1, 3, 7,15], 52)#[0, 1, 3, 7, 15], 52)
                self.run_suite([[['red', 'nocheatX', 'above'], ['green', 'nocheatO', 'below']], 1], [[[['orange', 'nocheatX', 'above'], ['green', 'nocheatO', 'below']], 1]], str(self.data_file_index), 3, [0, 1, 3, 7,15], 52)#[0, 1, 3, 7, 15], 52)

                self.data_file_index += 1

        elif SIM_ID == 7:
        # No cheat feature monocolor

            dim_index = 0
            for i in range(len(self.model.color_vectors['red'])):
                self.model.COLOR_DIMENSIONS.append(dim_index)
                dim_index += 1

            for i in range(len(self.model.shape_vectors['cheatXabove'])):
                self.model.SHAPE_DIMENSIONS.append(dim_index)
                dim_index += 1

            for i in range(len(self.model.relation_vectors['above'])):
                self.model.RELATION_DIMENSIONS.append(dim_index)
                dim_index += 1

            self.model.non_relation_dimensions = self.model.COLOR_DIMENSIONS + self.model.SHAPE_DIMENSIONS
            self.model.salience = [1] * 18 + [1] * 27 + [1]*2

            num_subjects = 32
            for subject in range(num_subjects):
                csv_file_name = str(self.data_file_index) + '.csv'
                csv_data_file = open('data/' + csv_file_name, 'a', encoding='UTF8')
                writer = csv.writer(csv_data_file, delimiter=',')
                writer.writerow(['resp.corr', 'total_setsize', 'trial_type', 'resp.rt', 'dcolor', 'participant'])
                csv_data_file.close()
                self.run_suite([[['red', 'nocheatX', 'above'], ['red', 'nocheatO', 'below']], 1], [[[['red', 'nocheatO', 'above'], ['red', 'nocheatX', 'below']], 1]], str(self.data_file_index), 1, [0, 1, 3, 7, 15], 52)
                self.run_suite([[['red', 'nocheatX', 'above'], ['red', 'nocheatO', 'below']], 1], [[[['orange', 'nocheatO', 'above'], ['orange', 'nocheatX', 'below']], 1]], str(self.data_file_index), 2, [0, 1, 3, 7, 15], 52)
                self.run_suite([[['red', 'nocheatX', 'above'], ['red', 'nocheatO', 'below']], 1], [[[['orange', 'nocheatX', 'above'], ['orange', 'nocheatO', 'below']], 1]], str(self.data_file_index), 3,  [0, 1, 3, 7, 15], 52)
                self.data_file_index += 1


        # Cheat feature multicolor (salience and other parameters are set elsewhere according to the )
        elif SIM_ID == 8:

            dim_index = 0
            for i in range(len(self.model.color_vectors['red'])):
                self.model.COLOR_DIMENSIONS.append(dim_index)
                dim_index += 1

            for i in range(len(self.model.shape_vectors['cheatXabove'])):
                self.model.SHAPE_DIMENSIONS.append(dim_index)
                dim_index += 1

            for i in range(len(self.model.relation_vectors['above'])):
                self.model.RELATION_DIMENSIONS.append(dim_index)
                dim_index += 1

            self.model.non_relation_dimensions = self.model.COLOR_DIMENSIONS + self.model.SHAPE_DIMENSIONS
            self.model.salience = [1] * 18 + [1] * 27 + [1]*2

            num_subjects = 32
            for subject in range(num_subjects):
                csv_file_name = str(self.data_file_index) + '.csv'
                csv_data_file = open('data/' + csv_file_name, 'a', encoding='UTF8')
                writer = csv.writer(csv_data_file, delimiter=',')
                writer.writerow(['resp.corr', 'total_setsize', 'trial_type', 'resp.rt', 'dcolor', 'participant'])
                csv_data_file.close()
                self.run_suite([[['red', 'cheatXabove', 'above'], ['green', 'cheatObelow', 'below']], 1], [[[['green', 'cheatOabove', 'above'], ['red', 'cheatXbelow', 'below']], 1]], str(self.data_file_index), 1, [0, 1, 3, 7, 15], 52)
                self.run_suite([[['red', 'cheatXabove', 'above'], ['green', 'cheatObelow', 'below']], 1], [[[['green', 'cheatOabove', 'above'], ['orange', 'cheatXbelow', 'below']], 1]], str(self.data_file_index), 2, [0, 1, 3, 7, 15], 52)
                self.run_suite([[['red', 'cheatXabove', 'above'], ['green', 'cheatObelow', 'below']], 1], [[[['orange', 'cheatXabove', 'above'], ['green', 'cheatObelow', 'below']], 1]], str(self.data_file_index), 3, [0, 1, 3, 7, 15], 52)
                self.data_file_index += 1

        # Cheat feeture multicolor reduced salience

        elif SIM_ID == 9:
            dim_index = 0

            for i in range(len(self.model.color_vectors['red'])):
                self.model.COLOR_DIMENSIONS.append(dim_index)
                dim_index += 1

            for i in range(len(self.model.shape_vectors['cheatXabove'])):
                self.model.SHAPE_DIMENSIONS.append(dim_index)
                dim_index += 1
            for i in range(len(self.model.relation_vectors['above'])):
                self.model.RELATION_DIMENSIONS.append(dim_index)
                dim_index += 1

            self.model.non_relation_dimensions = self.model.COLOR_DIMENSIONS + self.model.SHAPE_DIMENSIONS
            self.model.salience = [1] * 18 + [1] * 27 + [0.33] * 2
            num_subjects = 32

            for subject in range(num_subjects):
                csv_file_name = str(self.data_file_index) + '.csv'
                csv_data_file = open('data/' + csv_file_name, 'a', encoding='UTF8')
                writer = csv.writer(csv_data_file, delimiter=',')
                writer.writerow(['resp.corr', 'total_setsize', 'trial_type', 'resp.rt', 'dcolor', 'participant'])
                csv_data_file.close()
                self.run_suite([[['red', 'cheatXabove', 'above'], ['green', 'cheatObelow', 'below']], 1], [[[['green', 'cheatOabove', 'above'], ['red', 'cheatXbelow', 'below']], 1]], str(self.data_file_index), 1, [0, 1, 3, 7, 15], 52)
                self.run_suite([[['red', 'cheatXabove', 'above'], ['green', 'cheatObelow', 'below']], 1], [[[['green', 'cheatOabove', 'above'], ['orange', 'cheatXbelow', 'below']], 1]], str(self.data_file_index), 2, [0, 1, 3, 7, 15], 52)
                self.run_suite([[['red', 'cheatXabove', 'above'], ['green', 'cheatObelow', 'below']], 1], [[[['orange', 'cheatXabove', 'above'], ['green', 'cheatObelow', 'below']], 1]], str(self.data_file_index), 3, [0, 1, 3, 7, 15], 52)
                self.data_file_index += 1


        # Cheat featire monocolor


        elif SIM_ID == 10:

            dim_index = 0
            for i in range(len(self.model.color_vectors['red'])):
                self.model.COLOR_DIMENSIONS.append(dim_index)
                dim_index += 1

            for i in range(len(self.model.shape_vectors['cheatXabove'])):
                self.model.SHAPE_DIMENSIONS.append(dim_index)
                dim_index += 1

            for i in range(len(self.model.relation_vectors['above'])):
                self.model.RELATION_DIMENSIONS.append(dim_index)
                dim_index += 1

            self.model.non_relation_dimensions = self.model.COLOR_DIMENSIONS + self.model.SHAPE_DIMENSIONS
            self.model.salience = [1] * 18 + [1] * 27 + [1] * 2

            num_subjects = 32
            for subject in range(num_subjects):
                csv_file_name = str(self.data_file_index) + '.csv'
                csv_data_file = open('data/' + csv_file_name, 'a', encoding='UTF8')
                writer = csv.writer(csv_data_file, delimiter=',')
                writer.writerow(['resp.corr', 'total_setsize', 'trial_type', 'resp.rt', 'dcolor', 'participant'])
                csv_data_file.close()
                self.run_suite([[['red', 'cheatXabove', 'above'], ['red', 'cheatObelow', 'below']], 1], [[[['red', 'cheatOabove', 'above'], ['red', 'cheatXbelow', 'below']], 1]], str(self.data_file_index), 1, [0, 1, 3, 7, 15], 52)
                self.run_suite([[['red', 'cheatXabove', 'above'], ['red', 'cheatObelow', 'below']], 1], [[[['orange', 'cheatOabove', 'above'], ['orange', 'cheatXbelow', 'below']], 1]], str(self.data_file_index), 2, [0, 1, 3, 7, 15], 52)
                self.run_suite([[['red', 'cheatXabove', 'above'], ['red', 'cheatObelow', 'below']], 1], [[[['orange', 'cheatXabove', 'above'], ['orange', 'cheatObelow', 'below']], 1]], str(self.data_file_index), 3,  [0, 1, 3, 7, 15], 52)

                self.data_file_index += 1

        # No emergent cheat feature in Relation + feature and Feature-only conditions
        elif SIM_ID == 11:

            dim_index = 0
            for i in range(len(self.model.color_vectors['red'])):
                self.model.COLOR_DIMENSIONS.append(dim_index)
                dim_index += 1

            for i in range(len(self.model.shape_vectors['cheatXabove'])):
                self.model.SHAPE_DIMENSIONS.append(dim_index)
                dim_index += 1

            for i in range(len(self.model.relation_vectors['above'])):
                self.model.RELATION_DIMENSIONS.append(dim_index)
                dim_index += 1

            self.model.non_relation_dimensions = self.model.COLOR_DIMENSIONS + self.model.SHAPE_DIMENSIONS
            self.model.salience = [1] * 18 + [1] * 27 + [1] * 2

            num_subjects = 32
            for subject in range(num_subjects):
                csv_file_name = str(self.data_file_index) + '.csv'
                csv_data_file = open('data/' + csv_file_name, 'a', encoding='UTF8')
                writer = csv.writer(csv_data_file, delimiter=',')
                writer.writerow(['resp.corr', 'total_setsize', 'trial_type', 'resp.rt', 'dcolor', 'participant'])
                csv_data_file.close()
                self.run_suite([[['red', 'cheatXabove', 'above'], ['red', 'cheatObelow', 'below']], 1], [[[['red', 'cheatOabove', 'above'], ['red', 'cheatXbelow', 'below']], 1]], str(self.data_file_index), 1, [0, 1, 3, 7, 15], 52)
                self.run_suite([[['red', 'nocheatX', 'above'], ['red', 'nocheatO', 'below']], 1], [[[['orange', 'nocheatO', 'above'], ['orange', 'nocheatX', 'below']], 1]], str(self.data_file_index), 2, [0, 1, 3, 7, 15], 52)
                self.run_suite([[['red', 'nocheatX', 'above'], ['red', 'nocheatO', 'below']], 1], [[[['orange', 'nocheatX', 'above'], ['orange', 'nocheatO', 'below']], 1]], str(self.data_file_index), 3, [0, 1, 3, 7, 15], 52)
                self.data_file_index += 1


        elif SIM_ID ==12:

            dim_index = 0
            for i in range(len(self.model.color_vectors['red'])):
                self.model.COLOR_DIMENSIONS.append(dim_index)
                dim_index += 1

            for i in range(len(self.model.shape_vectors['cheatXabove'])):
                self.model.SHAPE_DIMENSIONS.append(dim_index)
                dim_index += 1

            for i in range(len(self.model.relation_vectors['above'])):
                self.model.RELATION_DIMENSIONS.append(dim_index)
                dim_index += 1

            self.model.non_relation_dimensions = self.model.COLOR_DIMENSIONS + self.model.SHAPE_DIMENSIONS
            self.model.salience = [1] * 18 + [1] * 27 + [0.33] * 2

            num_subjects = 32
            for subject in range(num_subjects):
                csv_file_name = str(self.data_file_index) + '.csv'
                csv_data_file = open('data/' + csv_file_name, 'a', encoding='UTF8')
                writer = csv.writer(csv_data_file, delimiter=',')
                writer.writerow(['resp.corr', 'total_setsize', 'trial_type', 'resp.rt', 'dcolor', 'participant'])
                csv_data_file.close()
                self.run_suite([[['red', 'cheatXabove', 'above'], ['green', 'cheatObelow', 'below']], 1], [[[['green', 'cheatOabove', 'above'], ['red', 'cheatXbelow', 'below']], 1]], str(self.data_file_index), 1, [0, 1, 3, 7, 15], 52)
                self.run_suite([[['red', 'cheatXabove', 'above'], ['green', 'cheatObelow', 'below']], 1], [[[['green', 'cheatOabove', 'above'], ['orange', 'cheatXbelow', 'below']], 1]], str(self.data_file_index), 2, [0, 1, 3, 7, 15], 52)
                self.run_suite([[['red', 'cheatXabove', 'above'], ['green', 'cheatObelow', 'below']], 1], [[[['orange', 'cheatXabove', 'above'], ['green', 'cheatObelow', 'below']], 1]], str(self.data_file_index), 3, [0, 1, 3, 7, 15], 52)
                self.data_file_index += 1




        # # Cheat feature multicolor SPACED OUT like Experiment 4b
        # # THE INTERFACE WILL SET RELEVANT SAMPLING TO 0.95 TO RUN THIS SIMULATION
        # elif SIM_ID == 11:
        #     num_subjects = 32
        #     for subject in range(num_subjects):
        #         csv_file_name = str(self.data_file_index) + '.csv'
        #         csv_data_file = open('data/' + csv_file_name, 'a', encoding='UTF8')
        #         writer = csv.writer(csv_data_file, delimiter=',')
        #         writer.writerow(['resp.corr', 'total_setsize', 'trial_type', 'resp.rt', 'dcolor', 'participant'])
        #         csv_data_file.close()
        #         self.run_suite([[['red', 'cheatXabove', 'above'], ['green', 'cheatObelow', 'below']], 1], [[[['green', 'cheatOabove', 'above'], ['red', 'cheatXbelow', 'below']], 1]], str(self.data_file_index), 1, [0, 1, 3, 7], 52)
        #         self.run_suite([[['red', 'cheatXabove', 'above'], ['green', 'cheatObelow', 'below']], 1], [[[['green', 'cheatOabove', 'above'], ['orange', 'cheatXbelow', 'below']], 1]], str(self.data_file_index), 2, [0, 1, 3, 7], 52)
        #         self.run_suite([[['red', 'cheatXabove', 'above'], ['green', 'cheatObelow', 'below']], 1], [[[['orange', 'cheatXabove', 'above'], ['green', 'cheatObelow', 'below']], 1]], str(self.data_file_index), 3, [0, 1, 3, 7], 52)
        #         self.data_file_index += 1


        # TODO THESE SHOULD BE DELETED THEY ARE REDUNDANT
        # num_subjects = 32
        # for subject in range(num_subjects):
        #     csv_file_name = str(self.data_file_index) + '.csv'
        #     csv_data_file = open('data/' + csv_file_name, 'a', encoding='UTF8')
        #     writer = csv.writer(csv_data_file, delimiter=',')
        #     writer.writerow(['resp.corr', 'total_setsize', 'trial_type', 'resp.rt', 'dcolor', 'participant'])
        #     csv_data_file.close()
        #     #self.run_suite([[['red', 'X', 'above'], ['green', 'O', 'below']], 1], [[[['green','O', 'above'],['red', 'X', 'below']], 1]], str(self.data_file_index), 1, [0, 1, 3, 7, 15], 52)
        #     #self.run_suite([[['red', 'X', 'above'], ['green', 'O', 'below']], 1], [[[['green', 'O', 'above'], ['orange', 'X', 'below']], 1]], str(self.data_file_index), 2, [0, 1, 3, 7, 15], 52)
        #     #self.run_suite([[['red', 'X', 'above'], ['green', 'O', 'below']], 1], [[[['orange', 'X', 'above'], ['green', 'O', 'below']], 1]], str(self.data_file_index), 3, [0, 1, 3, 7, 15], 52)
        #     self.run_suite([[['red', 'cheatXabove', 'above'], ['green', 'cheatObelow', 'below']], 1], [[[['green','cheatOabove', 'above'],['red', 'cheatXbelow', 'below']], 1]], str(self.data_file_index), 1, [0, 1, 3, 7, 15], 52)
        #     self.run_suite([[['red', 'cheatXabove', 'above'], ['green', 'cheatObelow', 'below']], 1], [[[['green', 'cheatOabove', 'above'], ['orange', 'cheatXbelow', 'below']], 1]], str(self.data_file_index), 2, [0, 1, 3, 7, 15], 52)
        #     self.run_suite([[['red', 'cheatXabove', 'above'], ['green', 'cheatObelow', 'below']], 1], [[[['orange', 'cheatXabove', 'above'], ['green', 'cheatObelow', 'below']], 1]], str(self.data_file_index), 3, [0, 1, 3, 7, 15], 52)
        #     #self.run_suite([[['red', 'nocheatX', 'above'], ['green', 'nocheatO', 'below']], 1], [[[['green','nocheatO', 'above'],['red', 'nocheatX', 'below']], 1]], str(self.data_file_index), 1, [0, 1, 3, 7, 15], 52)
        #     #self.run_suite([[['red', 'nocheatX', 'above'], ['green', 'nocheatO', 'below']], 1], [[[['green', 'nocheatO', 'above'], ['orange', 'nocheatX', 'below']], 1]], str(self.data_file_index), 2, [0, 1, 3, 7, 15], 52)
        #     #self.run_suite([[['red', 'nocheatX', 'above'], ['green', 'nocheatO', 'below']], 1], [[[['orange', 'nocheatX', 'above'], ['green', 'nocheatO', 'below']], 1]], str(self.data_file_index), 3, [0, 1, 3, 7, 15], 52)
        #     self.data_file_index += 1


        # num_subjects = 32
        # for subject in range(num_subjects):
        #     csv_file_name = str(self.data_file_index) + '.csv'
        #     csv_data_file = open('data/' + csv_file_name, 'a', encoding='UTF8')
        #     writer = csv.writer(csv_data_file, delimiter=',')
        #     writer.writerow(['resp.corr', 'total_setsize', 'trial_type', 'resp.rt', 'dcolor', 'participant'])
        #     csv_data_file.close()
        #     self.run_suite([[['red', 'cheatXabove', 'above'], ['red', 'cheatObelow', 'below']], 1], [[[['red', 'cheatOabove', 'above'], ['red', 'cheatXbelow', 'below']], 1]], str(self.data_file_index), 1, [0, 1, 3, 7, 15], 52)
        #     #self.run_suite([[['red', 'cheatXabove', 'above'], ['red', 'cheatObelow', 'below']], 1], [[[['orange', 'cheatOabove', 'above'], ['orange', 'cheatXbelow', 'below']], 1]], str(self.data_file_index), 2, [0, 1, 3, 7, 15], 52)
        #     #self.run_suite([[['red', 'cheatXabove', 'above'], ['red', 'cheatObelow', 'below']], 1], [[[['orange', 'cheatXabove', 'above'], ['orange', 'cheatObelow', 'below']], 1]], str(self.data_file_index), 3,  [0, 1, 3, 7, 15], 52)
        #
        #     #self.run_suite([[['red', 'nocheatX', 'above'], ['red', 'nocheatO', 'below']], 1], [[[['red', 'nocheatO', 'above'], ['red', 'nocheatX', 'below']], 1]], str(self.data_file_index), 1, [0, 1, 3, 7], 52)
        #     self.run_suite([[['red', 'nocheatX', 'above'], ['red', 'nocheatO', 'below']], 1], [[[['orange', 'nocheatO', 'above'], ['orange', 'nocheatX', 'below']], 1]], str(self.data_file_index), 2, [0, 1, 3, 7, 15], 52)
        #     self.run_suite([[['red', 'nocheatX', 'above'], ['red', 'nocheatO', 'below']], 1], [[[['orange', 'nocheatX', 'above'], ['orange', 'nocheatO', 'below']], 1]], str(self.data_file_index), 3,  [0, 1, 3, 7, 15], 52)
        #     self.data_file_index += 1



        #TODO THIS IS REDUNDANT AND SHOULD BE REMOVED
        # num_subjects = 32
        # for subject in range(num_subjects):
        #     csv_file_name = str(self.data_file_index) + '.csv'
        #     csv_data_file = open('data/' + csv_file_name, 'a', encoding='UTF8')
        #     writer = csv.writer(csv_data_file, delimiter=',')
        #     writer.writerow(['resp.corr', 'total_setsize', 'trial_type', 'resp.rt', 'dcolor', 'participant'])
        #     csv_data_file.close()
        #
        #     #
        #     #self.run_suite([[['red', 'cheatXabove', 'above'], ['red', 'cheatObelow', 'below']], 1], [[[['red', 'cheatOabove', 'above'], ['red', 'cheatXbelow', 'below']], 1]], str(self.data_file_index), 1, [0, 1, 3, 7, 15], 52)
        #     #self.run_suite([[['red', 'cheatXabove', 'above'], ['red', 'cheatObelow', 'below']], 1], [[[['orange', 'cheatOabove', 'above'], ['orange', 'cheatXbelow', 'below']], 1]], str(self.data_file_index), 2, [0, 1, 3, 7, 15], 52)
        #     #self.run_suite([[['red', 'cheatXabove', 'above'], ['red', 'cheatObelow', 'below']], 1], [[[['orange', 'cheatXabove', 'above'], ['orange', 'cheatObelow', 'below']], 1]], str(self.data_file_index), 3,  [0, 1, 3, 7, 15], 52)
        #
        #     self.run_suite([[['red', 'nocheatX', 'above'], ['red', 'nocheatO', 'below']], 1], [[[['red', 'nocheatO', 'above'], ['red', 'nocheatX', 'below']], 1]], str(self.data_file_index), 1, [0, 1, 3, 7, 15], 52)
        #     self.run_suite([[['red', 'nocheatX', 'above'], ['red', 'nocheatO', 'below']], 1], [[[['orange', 'nocheatO', 'above'], ['orange', 'nocheatX', 'below']], 1]], str(self.data_file_index), 2, [0, 1, 3, 7, 15], 52)
        #     self.run_suite([[['red', 'nocheatX', 'above'], ['red', 'nocheatO', 'below']], 1], [[[['orange', 'nocheatX', 'above'], ['orange', 'nocheatO', 'below']], 1]], str(self.data_file_index), 3,  [0, 1, 3, 7, 15], 52)
        #     self.data_file_index += 1


        # num_subjects = 32
        # for subject in range(num_subjects):
        #     csv_file_name = str(self.data_file_index) + '.csv'
        #     csv_data_file = open('data/' + csv_file_name, 'a', encoding='UTF8'):w

        #     writer = csv.writer(csv_data_file, delimiter=',')
        #     writer.writerow(['resp.corr', 'total_setsize', 'trial_type', 'resp.rt', 'dcolor', 'participant'])
        #     csv_data_file.close()
        #     self.run_suite([[['red', 'X', 'above'], ['red', 'O', 'below']], 1], [[[['red', 'O', 'above'], ['red', 'X', 'below']], 1]], str(self.data_file_index), 1, [0, 1, 3, 7, 15], 52)
        #     self.run_suite([[['red', 'X', 'above'], ['red', 'O', 'below']], 1], [[[['orange', 'O', 'above'], ['orange', 'X', 'below']], 1]], str(self.data_file_index), 2, [0, 1, 3, 7, 15], 52)
        #     self.run_suite([[['red', 'X', 'above'], ['red', 'O', 'below']], 1], [[[['orange', 'X', 'above'], ['orange', 'O', 'below']], 1]], str(self.data_file_index), 3,  [0, 1, 3, 7, 15], 52)
        #     self.data_file_index += 1
        # self.run_suite([[['green', 'X', 'above'], ['red', 'O', 'below']], 1], [[[['green','X', 'above'],['red', 'X', 'below']], 1]], 'Feature', [2, 4, 8, 16], 1000)
        # self.data_file_index += 1
        # self.run_suite([[['green', 'X', 'above'], ['red', 'O', 'below']], 1], [[[['green','X', 'above'],['orange', 'X', 'below']], 1]], 'Feature', [2, 4, 8, 16], 1000)
        # self.data_file_index += 1
        # self.run_suite([[['green', 'X', 'above'], ['red', 'O', 'below']], 1], [[[['green','X', 'above'],['yellow', 'X', 'below']], 1]], 'Feature', [2, 4, 8, 16], 1000)
        # self.data_file_index += 1
        # self.run_suite([[['green', 'X', 'above'], ['red', 'O', 'below']], 1], [[[['green','X', 'above'],['yellow', 'O', 'below']], 1]], 'Feature', [2, 4, 8, 16], 1000)
        # self.data_file_index += 1
        # self.run_suite([[['green', 'X', 'above'], ['green', 'O', 'below']], 1], [[[['green','X', 'above'],['yellow', 'X', 'below']], 1]], 'Feature', [2, 4, 8, 16], 1000)
        # self.data_file_index += 1
        # self.run_suite([[['green', 'X', 'above'], ['yellow', 'O', 'below']], 1], [[[['yellow','X', 'above'],['yellow', 'O', 'below']], 1]], 'Feature', [2, 4, 8, 16], 1000)
        # self.data_file_index += 1
        # self.run_suite([[['white', 'X', 'above'],['black', 'O', 'below']],1], [[[['white', 'X','none']],1]], 'Feature', [2, 4, 8, 16, 32, 64], 1000)
        # self.data_file_index += 1
        # self.run_suite([[['white', 'X', 'none']], 1], [[[['white', 'X', 'above'], ['black', 'O', 'below']], 1]],  'Feature', [2, 4, 8, 16, 32, 64], 1000)
        # self.data_file_index += 1
        # self.run_suite([[['white', 'X', 'above'], ['black', 'O', 'below']], 1], [[[['black','O', 'above'],['white', 'X', 'below']], 1]], 'Feature', [2, 4, 8, 16, 32, 64], 1000)
        # self.data_file_index += 1

    # Relational seraches with feature cheats

        # Dual Color

        # num_subjects = 32
        # for subject in range(num_subjects):
        #     csv_file_name = str(self.data_file_index) + '.csv'
        #     csv_data_file = open('data/' + csv_file_name, 'a', encoding='UTF8')
        #     writer = csv.writer(csv_data_file, delimiter=',')
        #     writer.writerow(['resp.corr', 'total_setsize', 'trial_type', 'resp.rt', 'dcolor', 'participant'])
        #     csv_data_file.close()
        #     self.run_suite([[['red', 'cheatXabove', 'above'], ['green', 'cheatObelow', 'below']], 1], [[[['green','cheatOabove', 'above'],['red', 'cheatXbelow', 'below']], 1]], str(self.data_file_index), 1, [0, 1, 3, 7, 15], 52)
        #     self.run_suite([[['red', 'cheatXabove', 'above'], ['green', 'cheatObelow', 'below']], 1], [[[['green', 'cheatOabove', 'above'], ['orange', 'cheatXbelow', 'below']], 1]], str(self.data_file_index), 2, [0, 1, 3, 7, 15], 52)
        #     self.run_suite([[['red', 'cheatXabove', 'above'], ['green', 'cheatObelow', 'below']], 1], [[[['orange', 'cheatXabove', 'above'], ['green', 'cheatObelow', 'below']], 1]], str(self.data_file_index), 3, [0, 1, 3, 7, 15], 52)
        #
        #     self.data_file_index += 1

        # Monocolor
        # num_subjects = 32
        # for subject in range(num_subjects):
        #     csv_file_name = str(self.data_file_index) + '.csv'
        #     csv_data_file = open('data/' + csv_file_name, 'a', encoding='UTF8')
        #     writer = csv.writer(csv_data_file, delimiter=',')
        #     writer.writerow(['resp.corr', 'total_setsize', 'trial_type', 'resp.rt', 'dcolor', 'participant'])
        #     csv_data_file.close()
        #     self.run_suite([[['red', 'cheatXabove', 'above'], ['red', 'cheatObelow', 'below']], 1], [[[['red', 'cheatOabove', 'above'], ['red', 'cheatXbelow', 'below']], 1]], str(self.data_file_index), 1, [0, 1, 3, 7, 15], 52)
        #     #self.run_suite([[['red', 'cheatXabove', 'above'], ['red', 'cheatObelow', 'below']], 1], [[[['orange', 'cheatOabove', 'above'], ['orange', 'cheatXbelow', 'below']], 1]], str(self.data_file_index), 2, [0, 1, 3, 7, 15], 52)
        #     #self.run_suite([[['red', 'cheatXabove', 'above'], ['red', 'cheatObelow', 'below']], 1], [[[['orange', 'cheatXabove', 'above'], ['orange', 'cheatObelow', 'below']], 1]], str(self.data_file_index), 3,  [0, 1, 3, 7, 15], 52)
        #     self.run_suite([[['red', 'nocheatX', 'above'], ['red', 'nocheatO', 'below']], 1],
        #                    [[[['orange', 'nocheatO', 'above'], ['orange', 'nocheatX', 'below']], 1]],
        #                    str(self.data_file_index), 2, [0, 1, 3, 7, 15], 52)
        #     self.run_suite([[['red', 'nocheatX', 'above'], ['red', 'nocheatO', 'below']], 1],
        #                    [[[['orange', 'nocheatX', 'above'], ['orange', 'nocheatO', 'below']], 1]],
        #                    str(self.data_file_index), 3, [0, 1, 3, 7, 15], 52)
        #     self.data_file_index += 1
        print(str(self.regression_summary_rts))
        self.graph_regression()

        # and finally, write the updated index to the file so it can be incremented next run
        self.write_file_index()

        exit()

    def graph_regression(self):

        """
        attempt to show graphs in graphic mode. if fail, then just curl up and die
        :return:
        """
        # ask whether user wants graphic run
        legal_responses = ('y', 'n')
        response = ''
        while not response in legal_responses:
            response = input('Graphic: (y)es or (n)o?')


        # otherwise TRY to run graphic, and note whether you failed
        if response == 'y':
            # if you don't already have the graphics handler, then try to create it
            if not self.graphics_handler:
                try:
                    self.graphics_handler = GraphicalRun1.GraphicalRun(self, 600, 800)
                except:
                    self.graphics_handler = None
                    self.graphics_failed  = True

            # if you have the graphics handler now, then run graphically
            if self.graphics_handler and not self.graphics_failed:
                self.graphics_handler.show_graphs(self.regression_summary_rts)





    def modify_parameters(self):
        """
        text-based method for parameter modification
        :return:
        """
        all_done = False
        while not all_done:
            # there are 20 possible responses: 19 parameters and Quit: list them
            legal_responses = []
            for i in range(20):
                legal_responses.append(i+1)

            parameter_list = self.write_parameters() # with no argument, this will return the text as a list to be printed
            for parameter in parameter_list:
                print( parameter)
            print
            print( '(19) Explain a parameter')
            print
            print( '(20) All Done')
            response = 0
            while not response in legal_responses:
                print
                response = input('Your choice (number) >')
                # now deal with the response
                if response == 20:
                    all_done = True
                elif response == 1:
                    self.model.TARGET_MATCH_THRESHOLD = input('TARGET_MATCH_THRESHOLD >')
                elif response == 2:
                    self.model.REJECTION_THRESHOLD = input('REJECTION_THRESHOLD >')
                elif response == 3:
                    self.model.TARGET_ABSENT_COST = input('TARGET_ABSENT_COST (int) >')
                elif response == 4:
                   self.model.P_RELEVANT_SAMPLING = input('P_RELEVANT_SAMPLING >')
                elif response == 5:
                    self.model.P_IRRELEVANT_SAMPLING = input('P_IRRELEVANT_SAMPLING >')
                elif response == 6:
                    self.model.MIN_SELECTION_PRIORITY = input('MIN_SELECTION_PRIORITY >')
                elif response == 7:
                    self.model.LINEAR_DISTANCE_COST = not(self.model.LINEAR_DISTANCE_COST)

                elif response == 8:
                    if self.model.LINEAR_DISTANCE_COST:
                        self.model.DISTANCE_AT_ZERO = input('DISTANCE_AT_ZERO (int) >')
                    else:
                        self.model.DISTANCE_FALLOFF_RATE = input('DISTANCE_FALLOFF_RATE >')

                elif response == 9:
                    self.model.RELEVANT_WEIGHT = input('RELEVANT_WEIGHT >')
                elif response == 10:
                    self.model.IRRELEVANT_WEIGHT = input('IRRELEVANT_WEIGHT >')
                elif response == 11:
                    self.model.COSINE_THRESHOLD = input('COSINE_THRESHOLD >')
                elif response == 12:
                    self.model.ATTENTION_SHIFT_COST = input('ATTENTION_SHIFT_COST (int) >')
                elif response == 13:
                    self.model.EYE_MOVEMENT_TIME_COST = input('EYE_MOVEMENT_TIME_COST (int) >')
                elif response == 14:
                    self.model.INTEGRATOR_GUIDED_PRIORITY = input('INTEGRATOR_GUIDED_PRIORITY >')
                elif response == 15:
                    self.model.PERMIT_EYE_MOVEMENTS = not(self.model.PERMIT_EYE_MOVEMENTS)
                elif response == 16:
                    self.model.ITEM_RADIUS = input('ITEM_RADIUS (int) >')
                elif response == 17:
                    self.model.ITEM_DISTANCE = input('ITEM_DISTANCE (int) >')
                elif response == 18:
                    self.model.CARTESIAN_GRID = not(self.model.CARTESIAN_GRID)
                elif response == 19:
                    explain_which = input('Number of parameter to explain (1...18) >')
                    self.write_parameter_description(explain_which)

    def save_distance_cost(self):
        """
        based on current parameters, computes and saves the distance cost for distances from fixation
        :return:
        """
        cost_list = [] # will be a list of tuples [dist,cost], where dist is in pixels and cost a float
        dist_increment = self.model.DISPLAY_RADIUS/5 # compute five distances per radius
        distance = 0
        while distance <= (self.model.DISPLAY_RADIUS * 2): # compute to distances = whole diameter
            # the cost is the distance cost as computed by the model for an item at this distance
            # the actual code from SearchModel1 (last modified 2/11/19):
            # scaled_distance = self.DISTANCE_FALLOFF_RATE * (float(item.fix_dist)/self.DISPLAY_RADIUS)
            # item.dist_wt = 1.0/(1.0 + scaled_distance)
            scaled_distance = self.model.DISTANCE_FALLOFF_RATE * (float(distance)/self.model.DISPLAY_RADIUS)
            distance_weight = 1.0/(1.0 + scaled_distance)
            cost_list.append(str(distance)+'\t%3f\n'%distance_weight)
            distance += dist_increment

        # now open the file, write the parameter values and write the cost list
        file_name = 'data/dist_cost_%.3f.txt'%self.model.DISTANCE_FALLOFF_RATE
        dist_file = open(file_name,'w')
        dist_file.write('Distance Cost Function for Parameters:\n')
        dist_file.write('Display radius = '+str(self.model.DISPLAY_RADIUS)+'\n')
        dist_file.write('DISTANCE_FALLOFF_RATE = %.3f\n\n'%self.model.DISTANCE_FALLOFF_RATE)
        dist_file.write('D\tWT\t (D = dist. (pixels); WT = distance_weight)\n')
        for cost in cost_list:
            dist_file.write(cost)
        dist_file.close()

        # and write the same data to the screen
        print( 'Distance cost data (weighting as a function of distance) saved to '+file_name)
        print
        print( 'D\tWt\n')
        for cost in cost_list:
            cost = cost.rstrip('\n') # strip off the final \n for screen printing
            print( cost)

    def get_menu_items(self):
        """
        returns a text list of menu items
        :return: 
        """
        text_lines = []
        text_lines.append('\n* * * Search Model * * *')
        text_lines.append('* *     Main Menu    * *\n')
        text_lines.append('(v) Verbose is ' + str(self.VERBOSE) + '. Toggle to ' + str(not (self.VERBOSE)) + '.')
        # text_lines.append('(g) Switch to graphics (there is no coming back)\n')
        #text_lines.append('\n(1) Run a ready-made simulation')
        text_lines.append('(1) Run a ready-made suite of simulations')
        #text_lines.append('\n(3) Make and run a new simulation')
        #text_lines.append('(4) Make and run a new suite of simulations\n')
        #text_lines.append('(5) Modify parameters\n')
        #text_lines.append('(6) Save distance cost\n')
        text_lines.append('(q) Quit\n')
        return text_lines

    def main_menu(self):
        """
        this is the main menu of the interface when it's run in non-graphical mode
        :return:
        """
        legal_responses = ('q','v','1')#,'2','3','4','5','6')
        all_done = False
        while not(all_done):
            text_lines = self.get_menu_items()
            for line in text_lines:
                print( line)

            response = ''
            while not response in legal_responses:
                response = input('<<<< Your desire? >>>>')

            if response == 'q': all_done = True
            elif response == 'v': self.VERBOSE = not(self.VERBOSE)
            elif response == 'g':
                return True # True here means Go to the graphical menu
            elif response == '2':
                result = self.run_premade_simulation()
                if result:
                    print( 'I hope that was to your liking. If not, then try changing parameters.')
                    print
                else:
                    print( 'I see that went poorly. Perhaps you should rethink you life.')
                    print
            elif response == '1':
                self.run_premade_suite()
            elif response == '3':
                self.run_handmade_simulation()
            elif response == '4':
                self.run_handmade_suite()

            elif response == '5':
                self.run_suite_from_file()
            elif response == '6':
                self.save_distance_cost() # write distance cost functin to file

            else:
                # chide user for carelessness
                print
                print( 'Please enter only something in the set (case matters)'+str(legal_responses))

        return False # false here means You're all done: Don't go to graphics menu

# * * * * * * * * * * * * * * * * * * * * * * * * * * *
# * * * * * * * * * * * Main Body * * * * * * * * * * *
# * * * * * * * * * * * * * * * * * * * * * * * * * * *

# create the model and the interface
model = SearchModel1.SearchModel()
main_interface = SearchModelInterface(model)

main_interface.main_menu()

# close pygame, if it's open
if main_interface.graphics_handler:
    # TRY to close the graphics
    main_interface.graphics_handler.close_display()


