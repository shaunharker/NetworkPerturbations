import sys,json

network_spec_file=sys.argv[1]
pattern_spec_file=sys.argv[2]
results_file=sys.argv[3]
results_dict = dict([tuple(pair.split(':')) for pair in sys.argv[4].split() if pair])
nummatches=sys.argv[5]


if nummatches:
	results_dict["StableFCMatchesParameterCount"] = int(nummatches)

with open(network_spec_file,'r') as nf:
    networkstr = nf.read()

results_dict["Network"]=networkstr

if pattern_spec_file:
    with open(pattern_spec_file,'r') as pf:
        pattern = json.load(pf)
else:
    pattern = "None"

results_dict["PatternSpecification"]=pattern

json.dump(results_dict,open(results_file,'w'))
