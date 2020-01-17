import sys, getopt, requests, json, time

# This file was last modified on 2020-01-16
# This script retrieves a list of all devices for a network under an organization in meraki cloud and reboot them, using the interval given on the cli

def printusertext(p_message):
	#prints a line of text that is meant for the user to read
	#do not process these lines when chaining scripts
	print('@ %s' % p_message)

def printhelp():
	#prints help text

	printusertext("This is a script that reboots all devices in a specified network.")
	printusertext('')
	printusertext('Usage:')
	printusertext('python meraki-reboot-ap -k <API key> -o <org name> -n <network id> -t <seconds>')
	printusertext('')
	printusertext('Use double quotes ("") in Windows to pass arguments containing spaces. Names are case-sensitive.')

def getorgid(p_apikey, p_orgname):
	#looks up org id for a specific org name
	#on failure returns 'null'

	r = requests.get('https://dashboard.meraki.com/api/v0/organizations', headers={'X-Cisco-Meraki-API-Key': p_apikey, 'Content-Type': 'application/json'})

	if r.status_code != requests.codes.ok:
		return 'null'

	rjson = r.json()

	for record in rjson:
		if record['name'] == p_orgname:
			return record['id']
	return('null')

def getshardurl(p_apikey, p_orgid):
	#Looks up shard URL for a specific org. Use this URL instead of 'dashboard.meraki.com'
	# when making API calls with API accounts that can access multiple orgs.
	#On failure returns 'null'

	r = requests.get('https://dashboard.meraki.com/api/v0/organizations/%s/snmp' % p_orgid, headers={'X-Cisco-Meraki-API-Key': p_apikey, 'Content-Type': 'application/json'})

	if r.status_code != requests.codes.ok:
		return 'null'

	rjson = r.json()

	return(rjson['hostname'])

def getdevicelist(p_apikey, p_shardurl, p_nwid):
	#returns a list of all devices in a network

	r = requests.get('https://%s/api/v0/networks/%s/devices' % (p_shardurl, p_nwid), headers={'X-Cisco-Meraki-API-Key': p_apikey, 'Content-Type': 'application/json'})

	returnvalue = []
	if r.status_code != requests.codes.ok:
		returnvalue.append({'serial': 'null', 'model': 'null'})
		return(returnvalue)

	return(r.json())

def main(argv):
	#get command line arguments
	arg_apikey = 'null'
	arg_orgname = 'null'
	arg_network = 'null'
	arg_interval = 'null'

	try:
		opts, args = getopt.getopt(argv, 'hk:o:n:f:t:')
	except getopt.GetoptError:
		printhelp()
		sys.exit(2)

	for opt, arg in opts:
		if opt == '-h':
			printhelp()
			sys.exit()
		elif opt == '-k':
			arg_apikey = arg
		elif opt == '-o':
			arg_orgname = arg
		elif opt == '-n':
			arg_network = arg
		elif opt == '-t':
			arg_interval = int(arg,10)

	if arg_apikey == 'null' or arg_orgname == 'null' or arg_network == 'null' or arg_interval == 'null':
		printhelp()
		sys.exit(2)

	#get organization id corresponding to org name provided by user
	orgid = getorgid(arg_apikey, arg_orgname)
	if orgid == 'null':
		printusertext('ERROR: Fetching organization failed')
		sys.exit(2)

	#get shard URL where Org is stored
	shardurl = getshardurl(arg_apikey, orgid)
	if shardurl == 'null':
		printusertext('ERROR: Fetching Meraki cloud shard URL failed')
		sys.exit(2)

	#get devices' list
	devicelist = getdevicelist(arg_apikey, shardurl, arg_network)

	# uncomment if desire to print the devicelist
    #for i in range (0, len(devicelist)):
		# MODIFY THE LINE BELOW TO CHANGE OUTPUT FORMAT
		#print('%s,%s' % (devicelist[i]['serial'], devicelist[i]['model']))

	#reboot AP on the device list
	for i in range (0, len(devicelist)):
		reboot_ap = requests.post('https://%s/api/v0/networks/%s/devices/%s/reboot' % (shardurl, arg_network, devicelist[i]['serial']), headers={'X-Cisco-Meraki-API-Key': arg_apikey, 'Content-Type': 'application/json'})

		print(devicelist[i]['serial'],reboot_ap.status_code)

		# time to wait between reboot
		time.sleep(arg_interval)

if __name__ == '__main__':
	main(sys.argv[1:])
