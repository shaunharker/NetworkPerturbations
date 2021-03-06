from callandanswer import getinfo
import networkperturbations as perturb
import fileparsers,ExtremaPO
import subprocess, os, json, itertools,sys


class Job():

    def __init__(self,run_type="qsub",params={}):
        # use qsub (conley3) or sbatch (hpcc/fen2) or local (mac os x, my install) as run_type
        self.run_type = run_type
        if run_type in ["qsub", "local"]:
            self.maindir = ""
        elif run_type=="sbatch":
            self.maindir = "/scratch/bc567" # eventually this needs to be in callandanswer.py
        if not params:
            # collect parameters
            self.params = getinfo()
        else:
            self.params = params

    def prep(self):
        # set up folders for calculations
        self._makedirectories()
        # do perturbations if not already done
        if 'numperturbations' in self.params:
            self._parsefilesforperturbation()
            networks = perturb.perturbNetwork(self.params)
        else:
            networks = None
        # make patterns if desired and not already done
        if 'timeseriesfile' in self.params:
            # must return network uid for each pattern
            uids,patterns = self._makepatterns(networks)
        else:
            uids,patterns = None,None
        # save networks and patterns, if any
        self._savefiles(networks,patterns,uids)

    def run(self):
        # shell call to scheduler (or serial if "local")
        if self.params['removeDB'] == 'y': RMDB = "True"
        else: RMDB = "False"
        if self.params['removeNF'] == 'y': RMNF = "True"
        else: RMNF = "False"
        if not self.params['queryfile']: self.params['queryfile'] = 'shellscripts/blankquery.sh'
        shellcall = ["shellscripts/networkperturbations.sh " + " ".join([self.params['dsgrn'],self.NETWORKDIR,self.PATTERNDIR, self.DATABASEDIR, self.RESULTSDIR, self.params['queryfile'],"shellscripts/networkperturbations_helper_"+self.run_type+".sh",self.run_type, RMDB, RMNF])]
        subprocess.call(shellcall,shell=True)

    def _makedirectories(self):
        # use datetime as unique identifier to avoid overwriting
        DATETIME = subprocess.check_output(['date +%Y_%m_%d_%H_%M_%S'],shell=True).strip()
        path = os.path.join(self.maindir,"computations"+DATETIME)

        if 'networkfolder' in self.params:
            self.NETWORKDIR=self.params['networkfolder']
            if 'patternfolder' in self.params:
                self.PATTERNDIR=self.params['patternfolder']
            else:
                self.PATTERNDIR = os.path.join(path,"patterns")
                subprocess.call(['mkdir -p ' + self.PATTERNDIR],shell=True)
        else:
            self.NETWORKDIR =os.path.join(path,"networks")
            subprocess.call(['mkdir -p ' + self.NETWORKDIR],shell=True)
            self.PATTERNDIR =os.path.join(path,"patterns")
            subprocess.call(['mkdir -p ' + self.PATTERNDIR],shell=True)

        self.DATABASEDIR=os.path.join(path,"databases")
        self.RESULTSDIR =os.path.join(path,"results")
        subprocess.call(['mkdir -p ' + self.DATABASEDIR],shell=True)
        subprocess.call(['mkdir -p ' + self.RESULTSDIR],shell=True)

    def _parsefilesforperturbation(self):
        network_spec = open(self.params['networkfile'],'r').read()
        while network_spec[-1]=='\n': network_spec = network_spec[:-1]
        self.params['network_spec'] = network_spec
        if 'edgefile' in self.params:
            self.params['edgelist'] = fileparsers.parseEdgeFile(self.params['edgefile'])
        else:
            self.params['edgelist'] = None
        if 'nodefile' in self.params:
            self.params['nodelist'] = fileparsers.parseNodeFile(self.params['nodefile'])
        else:
            self.params['nodelist'] = None

    def _makepatterns(self,networks=None):
        if networks is None:
            networklabels, uids = self._makenetworklabelsfromfiles()
        else:
            networklabels, uids = self._makenetworklabelsfromspecs(networks)
        uniqnetlab = list(set(networklabels))
        masterlabels, masterdata = self._parsetimeseries(set(itertools.chain.from_iterable(uniqnetlab)))
        uniqpatterns =[]
        for nl in uniqnetlab:
            ts_data = [masterdata[masterlabels.index(n)] for n in nl]
            uniqpatterns.append( ExtremaPO.makeJSONstring(ts_data,nl,n=1,scalingFactors=self.params['scaling_factors'],step=0.01) )
        patterns = [ uniqpatterns[uniqnetlab.index(nl)] for nl in networklabels ]
        return uids, patterns

    def _makenetworklabelsfromspecs(self,networks):
        return [ tuple([n.replace(':',' ').split()[0] for n in network_spec.split('\n') if n]) for network_spec in networks ], None

    def _makenetworklabelsfromfiles(self):
        networklabels=[]
        uids=[]
        for fname in os.listdir(self.params['networkfolder']):
            uids.append(''.join([c for c in fname if c.isdigit()]))
            networklabels.append(tuple([l.replace(':',' ').split()[0] for l in open(os.path.join(self.params['networkfolder'],fname),'r') if l]))
        return networklabels, uids

    def _parsetimeseries(self,desiredlabels):
        if self.params['ts_type'] == 'col':
            TSList,TSLabels,timeStepList = fileparsers.parseTimeSeriesFileCol(self.params['timeseriesfile'])
        elif self.params['ts_type'] == 'row':
            TSList,TSLabels,timeStepList = fileparsers.parseTimeSeriesFileRow(self.params['timeseriesfile'])
        if self.params['ts_truncation'] != float(-1):
            ind = timeStepList.index(self.params['ts_truncation'])
        else:
            ind = len(timeStepList)
        if not set(desiredlabels).issubset(TSLabels):
            raise ValueError("Missing time series for some nodes. Aborting.")
        labels,data = zip(*[(node,TSList[TSLabels.index(node)][:ind]) for node in TSLabels if node in desiredlabels])
        return labels,data

    def _savefiles(self,networks=None,patterns=None,networkuids=None):

        def savenetwork(uid,network_spec):
            nfile = os.path.join(self.NETWORKDIR, "network"+uid+".txt")
            open(nfile,'w').write(network_spec)

        def savepatterns(uid,pats):
            subdir = os.path.join(self.PATTERNDIR,uid)
            subprocess.call(['mkdir -p ' + subdir],shell=True)
            for (pat,scfc) in zip(pats,self.params['scaling_factors']):
                puid = '{:.{prec}f}'.format(scfc, prec=scfc_padding).replace('.','_')
                pfile = os.path.join(subdir, "pattern"+puid+".txt")
                json.dump(pat,open(pfile,'w'))

        if patterns is not None:
            scfc_padding = max(max([len(str(s)) for s in self.params['scaling_factors']])-2, 0)
            if networks is not None:
                N=len(str(len(networks)))
                for k,(network_spec,pats) in enumerate(zip(networks,patterns)):
                    # zero pad integer for unique id
                    uid = str(k).zfill(N)
                    savenetwork(uid,network_spec)
                    savepatterns(uid,pats)
            elif networkuids is not None:
                for (uid,pats) in zip(networkuids,patterns):
                    savepatterns(uid,pats)
            else:
                raise RuntimeError("Should not get here. Debug.")
        elif networks is not None:
            N=len(str(len(networks)))
            for k,network_spec in enumerate(networks):
                # zero pad integer for unique id
                uid = str(k).zfill(N)
                savenetwork(uid,network_spec)
       
        