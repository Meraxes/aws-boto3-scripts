import sys
import boto3
import datetime, time
from dateutil.tz import tzutc
from optparse import OptionParser

Parser = OptionParser()
Parser.add_option("-a", "--account", dest="AWSAccount",
                  help="AWS account / owner ID")
Parser.add_option("-p", "--profile", dest="AWSProfile",
                  help="""AWS credential profile name. Default will
                       be used if not provided.""")
Parser.add_option("-r", "--region", dest="AWSRegion",
                  help="AWS Region for client connection")

(Options, Args) = Parser.parse_args()


# Option validation and connection variable definitions
if Options.AWSAccount:
    AWSAccount = Options.AWSAccount
else:
    print("Please provide an AWS account / owner ID using -a or --account")
    sys.exit(1)
if Options.AWSProfile:
    AWSProfile = Options.AWSProfile
else:
    print("No credential profile provided, using default")
    AWSProfile = "default"
if Options.AWSRegion:
    AWSRegion = Options.AWSRegion
else:
    print("Please provide a valid AWS region using -r or --region")
    sys.exit(1)

# Establish boto3 session and client
try:
    Session = boto3.Session(profile_name=AWSProfile)
    Client = Session.client("ec2", region_name=AWSRegion)
except Exception as e:
    print("Error establishing boto3 client: {0}").format(e)
    sys.exit(1)

# Describe ec2 snapshots
try:
    Snapshots = Client.describe_snapshots(OwnerIds=[AWSAccount])
except Exception as e:
    print("Error in describing snapshots: {0}").format(e)
    sys.exit(1)

# Loop through snapshots and remove any older than 30 days
for Snapshot in Snapshots['Snapshots']:

    SnapshotCreated = Snapshot['StartTime']
    SnapshotCreatedEpoch = time.mktime(SnapshotCreated.timetuple())
    ExpirationDate = datetime.datetime.now() + datetime.timedelta(-31)
    ExpirationDateEpoch = time.mktime(ExpirationDate.timetuple())

    if SnapshotCreatedEpoch < ExpirationDateEpoch:
        print("Removing snapshot: {0}").format(Snapshot['SnapshotId'])
        try:
            print("Removing snapshot ({0})").format('SnapshotId')
            Results = Client.delete_snapshot(SnapshotId=Snapshot['SnapshotId'])
        except Exception as e:
            if "(InvalidSnapshot.InUse)" in str(e):
                continue
            else:
                print("Error in deleting snapshot ({0}): {1}").format(Snapshot['SnapshotId'], e)
                sys.exit(1)
