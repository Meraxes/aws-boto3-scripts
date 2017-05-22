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
    print("Please provide an AWS account / owner ID using -p or --profile")
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

# Establish boto3 session and clients
try:
    Session = boto3.Session(profile_name=AWSProfile)
    AutoScalingClient = Session.client("autoscaling", region_name=AWSRegion)
    Ec2Client = Session.client("ec2", region_name=AWSRegion)
except Exception as e:
    print("Error establishing boto3 client: {0}").format(e)
    sys.exit(1)

# Describe autoscaling launch configurations
# Describe ec2 instances
try:
    LaunchConfigs = AutoScalingClient.describe_launch_configurations()
    Instances = Ec2Client.describe_instances()
    Images = Ec2Client.describe_images(Owners=[AWSAccount])
except Exception as e:
    print("Error in describing resources: {0}").format(e)
    sys.exit(1)

# Loop through launch configurations and collate all images in use
ImagesInUse = []
for Config in LaunchConfigs['LaunchConfigurations']:
    ImagesInUse.append(Config['ImageId'])

# Loop through instances and collate images in use
for Reservation in Instances['Reservations']:
    for Instance in Reservation['Instances']:
        ImagesInUse.append(Instance['ImageId'])

# Remove duplicate image entries
ImagesInUse = list(set(ImagesInUse))

# Loop through existing images and remove if not in use
for Image in Images['Images']:
    ImageId = Image['ImageId']
    if ImageId in ImagesInUse:
        print("Image {0} in use").format(ImageId)
    else:
        print("Removing image {0}, not in use.").format(ImageId)
        try:
            Ec2Client.deregister_image(ImageId=ImageId)
        except Exception as e:
            print("Error deregistering image {0}").format(ImageId)
