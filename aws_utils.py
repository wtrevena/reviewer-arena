import boto3
import uuid
import datetime
import os

# Load AWS credentials from environment variables
aws_access_key_id = os.environ.get('AWS_ACCESS_KEY_ID')
aws_secret_access_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
aws_region = os.environ.get('AWS_REGION')

# Initialize the DynamoDB client
dynamodb = boto3.resource('dynamodb',
                          region_name=aws_region,
                          aws_access_key_id=aws_access_key_id,
                          aws_secret_access_key=aws_secret_access_key)

# Define the tables
requests_table = dynamodb.Table('reviewer_arena_requests')
leaderboards_table = dynamodb.Table('reviewer_arena_leaderboard')

# Function to write a request to the Requests table
def write_request(user_id, paper_id, model_a, model_b, vote):
    request_id = str(uuid.uuid4())
    timestamp = datetime.datetime.now().isoformat()
    
    response = requests_table.put_item(
        Item={
            'RequestID': request_id,
            'Timestamp': timestamp,
            'UserID': user_id,
            'PaperID': paper_id,
            'ModelA': model_a,
            'ModelB': model_b,
            'Vote': vote
        }
    )
    return response

# Function to update leaderboard after a vote
def update_leaderboard(model_a, model_b, vote):
    # Retrieve current stats for ModelA and ModelB
    model_a_stats = leaderboards_table.get_item(Key={'ModelID': model_a}).get('Item', {})
    model_b_stats = leaderboards_table.get_item(Key={'ModelID': model_b}).get('Item', {})
    
    # Initialize stats if they don't exist
    if not model_a_stats:
        model_a_stats = {'ModelID': model_a, 'Wins': 0, 'Losses': 0, 'Ties': 0, 'EloScore': 1200, 'Votes': 0}
    if not model_b_stats:
        model_b_stats = {'ModelID': model_b, 'Wins': 0, 'Losses': 0, 'Ties': 0, 'EloScore': 1200, 'Votes': 0}
    
    # Update stats based on the vote
    if vote == "A is better":
        model_a_stats['Wins'] += 1
        model_b_stats['Losses'] += 1
    elif vote == "B is better":
        model_a_stats['Losses'] += 1
        model_b_stats['Wins'] += 1
    elif vote == "Tie":
        model_a_stats['Ties'] += 1
        model_b_stats['Ties'] += 1
    model_a_stats['Votes'] += 1
    model_b_stats['Votes'] += 1
    
    # Calculate new Elo scores (simple Elo calculation for illustration)
    model_a_stats['EloScore'], model_b_stats['EloScore'] = calculate_elo(model_a_stats['EloScore'], model_b_stats['EloScore'], vote)
    
    # Write updated stats back to the Leaderboards table
    leaderboards_table.put_item(Item=model_a_stats)
    leaderboards_table.put_item(Item=model_b_stats)

# Function to calculate new Elo scores
def calculate_elo(elo_a, elo_b, vote, k=32):
    expected_a = 1 / (1 + 10 ** ((elo_b - elo_a) / 400))
    expected_b = 1 / (1 + 10 ** ((elo_a - elo_b) / 400))
    
    if vote == "A is better":
        actual_a = 1
        actual_b = 0
    elif vote == "B is better":
        actual_a = 0
        actual_b = 1
    else:  # Tie
        actual_a = 0.5
        actual_b = 0.5
    
    new_elo_a = elo_a + k * (actual_a - expected_a)
    new_elo_b = elo_b + k * (actual_b - expected_b)
    
    return round(new_elo_a), round(new_elo_b)

# Function to query leaderboard
def get_leaderboard():
    response = leaderboards_table.scan()
    leaderboard = response.get('Items', [])
    
    # Sort by EloScore in descending order
    leaderboard.sort(key=lambda x: x['EloScore'], reverse=True)
    
    return leaderboard
