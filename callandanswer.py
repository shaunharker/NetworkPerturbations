import os,sys

###########################################################
# All "gimme" functions are input checkers for getinfo().
###########################################################

def gimme_nonneg_int(inputstr,strictlypositive=False):

    err = "non-negative" if not strictlypositive else "positive"
    errormessage = "\nResponse not recognized. Please enter a " + err + " integer.  "

    success=False
    while not success:
        try:
            myint = int(inputstr)
            if (myint > 0)*(strictlypositive) or (myint >= 0)*(not strictlypositive):
                success = True
            else:
                inputstr = raw_input(errormessage)
        except:
            inputstr = raw_input(errormessage)

    return myint

def gimme_positive_or_minusone_float(inputstr):

    errormessage = "\nResponse not recognized. Please enter a floating point number.  "
   
    success = False
    while not success:
        try:
            myfloat = float(inputstr)
            if myfloat > 0 or myfloat == -1:
                success = True
            else:
                inputstr = raw_input(errormessage)
        except:
            inputstr = raw_input(errormessage)

    return myfloat

def gimme_floats_0_1(inputlist):
    # lists are input() instead of raw_input()

    errormessage = "\nResponse not recognized. Enter a list of floats between 0 and 1 inclusive.  "

    def checkbounds(inputlist):
        if not inputlist:
            return False
        newinputlist = []
        for s in inputlist:
            try:
                s = float(s)
                if s < 0 or s>1:
                    return False
                else:            
                    newinputlist.append(s)
            except:
                return False
        return newinputlist

    inputlist = checkbounds(inputlist)
    while not inputlist:
        inputlist = checkbounds(input(errormessage))
    return inputlist

def gimme_str_from_list(inputstr,correctinputs):
    while inputstr not in correctinputs:
        inputstr = raw_input("\nResponse not recognized. Please enter one of {}.  ".format(' or '.join(correctinputs)))
    return inputstr

def gimme_existing_path(inputstr,isfile=False):
    errormessage = "\nPath not found. Enter new path.  " if not isfile else "\nFile not found. Enter new file.  "
    thispath = os.path.expanduser(inputstr)
    while (not os.path.isdir(thispath))*(not isfile) and (not os.path.isfile(thispath))*isfile:
        thispath = os.path.expanduser(raw_input(errormessage))
    return thispath

def gimme_existing_path_skipOK(inputstr,isfile=False):
    if inputstr == "":
        return inputstr
    else:
        return gimme_existing_path(inputstr,isfile)

##########################################
# Request files and parameters from user.
##########################################

def getinfo():
    params = dict()

    # get path to DSGRN
    params['dsgrn'] = gimme_existing_path(raw_input("\nEnter the path of the DSGRN folder.  "),isfile=False)
    if not os.path.isdir(os.path.expanduser(os.path.join(params['dsgrn'],'software/Signatures'))):
        print "\n\nDSGRN has a non-standard file structure. Program cannot be completed.\n")
        sys.exit()

    # get network spec(s)
    netfolder = gimme_str_from_list(raw_input("\nAre your perturbations already constructed in a separate folder (y or n)?  "),['y','n'])
    if netfolder == 'y':
        # perturbations pre-calculated
        params['networkfolder'] = gimme_existing_path(raw_input("\nEnter the path of the network perturbations folder (each file within must have a uniquely identifying integer in the file name).  "),isfile=False)
    elif netfolder == 'n':
        # perturbations are not pre-calculated
        params['networkfile'] = gimme_existing_path(raw_input("\nGive the path to a file containing the network specification that is to be perturbed.  "),isfile=True)
        # get node and edge files
        param['nodefile'] = gimme_existing_path_skipOK(raw_input("\nIf you wish to perturb the network by adding node names from a file, enter the path to the file (leave blank otherwise).\nThe file should be pre-filtered to have only nodes acceptable in perturbations.  "),isfile=False)
        param['edgefile'] = gimme_existing_path_skipOK(raw_input("\nIf you wish to perturb the network by adding edges from a file, enter the path to the file (leave blank otherwise).\nThe file should be pre-filtered to have only edges acceptable in perturbations.  "),isfile=False)
        if not param['edgefile'] and not param['nodefile']:
            param['add_madeup_nodes'] = gimme_str_from_list(raw_input("\nWould you like to add anonymous nodes and edges to the network ('y') or just edges ('n')?  "),['y','n'])
        if param['edgefile'] and not param['nodefile']:
            print "\n\nNote: only edges will be added to the existing network (not nodes).\n"
        # how many perturbations
        params['numperturbations'] = gimme_nonneg_int(raw_input("\nHow many network perturbations do you want? Example: 1000.  " ),strictlypositive=True)
        # get max size of each database
        params['maxparams'] = gimme_nonneg_int(raw_input("\nHow many parameters will you admit per perturbation? Example: 200000.  "),strictlypositive=True)

    # choose database queries to perform; more can be added in a modular fashion
    params['stableFCs'] = gimme_str_from_list(raw_input("\nDo you want to know the number of parameters exhibiting at least one stable FC (y or n)?  "),['y','n']) 
    params['multistable']= gimme_str_from_list(raw_input("\nDo you want to know the number of parameters exhibiting more than one stable Morse set of any type (y or n)?  "),['y','n'])
    params['singlefpqueries'] = input("\nWould you like to make single FP queries? If so, enter a list of arguments. \nIncorrect format, state, or variable names will crash the process later. \nExample of two single queries: ['E2F 3 3 Rb 0 0', 'E2F 0 0 Rb 1 1']. Enter [] for no queries.  ")
    params['dualfpqueries'] = input("\nWould you like to query for the simultaneous presence of two FPs? If so, enter a list of arguments. \nIncorrect format, state, or variable names will crash the process later. \nExample of two dual queries: ['E2F 3 3 Rb 0 0 E2F 0 0 Rb 1 1', 'Myc 0 1 E2F 2 2 E2F 0 2 Rb 1 1']. Enter [] for no queries.  ")

    # choose whether to pattern match and get associated parameters
    patternmatch = gimme_str_from_list(raw_input("\nDo you want to pattern match (y or n)?  "),['y','n'])
    if patternmatch == 'y':
        if netfolder == 'y':
            patfolder = gimme_str_from_list(raw_input("\nAre your patterns already constructed in a separate folder (y or n)?  "),['y','n'])
            if patfolder == 'y':
                params['patternfolder'] = gimme_existing_path(raw_input("\nEnter the path of the patterns folder.  "),isfile=False)
        # the following is if, not elif
        if netfolder == 'n' or patfolder == 'n':
            params['timeseriesfile'] = gimme_existing_path(raw_input("\nGive the path to a file containing the time series data.  "),isfile=True)
            params['ts_type'] = gimme_str_from_list(raw_input("\nDo the time series occur in rows ('row') or columns ('col')?  "),['row','col'])
            params['ts_trunction'] = gimme_positive_or_minusone_float(raw_input("\nChoose a (positive) truncation time for the time series data, or the value -1 for no truncation.  "))
            params['scaling_factors'] = gimme_floats_0_1(input("\nGive a list of scaling factors (noise levels) between 0 and 1 to construct the patterns from the data. Example: [0.0, 0.05, 0.1, 0.15].  "))
    return params

if __name__ == '__main__':
    params = getinfo()
    print("\n")
    print params