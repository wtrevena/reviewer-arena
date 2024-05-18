import boto3
import uuid
import datetime
import os
from decimal import Decimal, getcontext
from dotenv import load_dotenv

try:
    load_dotenv()
except:
    pass

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
    timestamp = str(Decimal(datetime.datetime.now().timestamp()))
    
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
    # Map vote options to simpler keys
    vote_mapping = {
        "👍 A is better": "A is better",
        "👍 B is better": "B is better",
        "👔 Tie": "Tie",
        "👎 Both are bad": "Tie"  # Assuming "Both are bad" is treated as a tie
    }
    vote = vote_mapping.get(vote, "Tie")  # Default to "Tie" if vote is not found

    # Retrieve current stats for ModelA and ModelB
    model_a_stats = leaderboards_table.get_item(Key={'ModelID': model_a}).get('Item', {})
    model_b_stats = leaderboards_table.get_item(Key={'ModelID': model_b}).get('Item', {})
    
    # Initialize stats if they don't exist
    if not model_a_stats:
        model_a_stats = {'ModelID': model_a, 'Wins': 0, 'Losses': 0, 'Ties': 0, 'EloScore': Decimal(1200), 'Votes': 0}
        leaderboards_table.put_item(Item=model_a_stats)
    if not model_b_stats:
        model_b_stats = {'ModelID': model_b, 'Wins': 0, 'Losses': 0, 'Ties': 0, 'EloScore': Decimal(1200), 'Votes': 0}
        leaderboards_table.put_item(Item=model_b_stats)
    
    # Update stats based on the vote
    update_expressions = {
        "A is better": {
            "model_a": "SET Wins = Wins + :inc, Votes = Votes + :inc",
            "model_b": "SET Losses = Losses + :inc, Votes = Votes + :inc"
        },
        "B is better": {
            "model_a": "SET Losses = Losses + :inc, Votes = Votes + :inc",
            "model_b": "SET Wins = Wins + :inc, Votes = Votes + :inc"
        },
        "Tie": {
            "model_a": "SET Ties = Ties + :inc, Votes = Votes + :inc",
            "model_b": "SET Ties = Ties + :inc, Votes = Votes + :inc"
        }
    }
    
    expression_a = update_expressions[vote]["model_a"]
    expression_b = update_expressions[vote]["model_b"]
    
    # Update ModelA stats
    leaderboards_table.update_item(
        Key={'ModelID': model_a},
        UpdateExpression=expression_a,
        ExpressionAttributeValues={':inc': 1}
    )
    
    # Update ModelB stats
    leaderboards_table.update_item(
        Key={'ModelID': model_b},
        UpdateExpression=expression_b,
        ExpressionAttributeValues={':inc': 1}
    )
    
    # Calculate new Elo scores (simple Elo calculation for illustration)
    new_elo_a, new_elo_b = calculate_elo(model_a_stats['EloScore'], model_b_stats['EloScore'], vote)

    # Calculate 95% CI for new Elo scores
    ci_a_lower, ci_a_upper = calculate_95_ci(new_elo_a, model_a_stats['Votes'] + 1)
    ci_b_lower, ci_b_upper = calculate_95_ci(new_elo_b, model_b_stats['Votes'] + 1)

    # Update Elo scores and 95% CI
    leaderboards_table.update_item(
        Key={'ModelID': model_a},
        UpdateExpression="SET EloScore = :new_elo, CI_Lower = :ci_lower, CI_Upper = :ci_upper",
        ExpressionAttributeValues={':new_elo': Decimal(new_elo_a), ':ci_lower': Decimal(ci_a_lower), ':ci_upper': Decimal(ci_a_upper)}
    )

    leaderboards_table.update_item(
        Key={'ModelID': model_b},
        UpdateExpression="SET EloScore = :new_elo, CI_Lower = :ci_lower, CI_Upper = :ci_upper",
        ExpressionAttributeValues={':new_elo': Decimal(new_elo_b), ':ci_lower': Decimal(ci_b_lower), ':ci_upper': Decimal(ci_b_upper)}
    )

# Set the precision for Decimal
getcontext().prec = 28

# Function to calculate new Elo scores
def calculate_elo(elo_a, elo_b, vote, k=32):
    # Ensure elo_a and elo_b are Decimals
    elo_a = Decimal(elo_a)
    elo_b = Decimal(elo_b)
    
    expected_a = 1 / (1 + Decimal(10) ** ((elo_b - elo_a) / Decimal(400)))
    expected_b = 1 / (1 + Decimal(10) ** ((elo_a - elo_b) / Decimal(400)))
    
    if vote == "A is better":
        actual_a = Decimal(1)
        actual_b = Decimal(0)
    elif vote == "B is better":
        actual_a = Decimal(0)
        actual_b = Decimal(1)
    else:  # Tie
        actual_a = Decimal(0.5)
        actual_b = Decimal(0.5)
    
    new_elo_a = elo_a + Decimal(k) * (actual_a - expected_a)
    new_elo_b = elo_b + Decimal(k) * (actual_b - expected_b)
    
    return round(new_elo_a, 2), round(new_elo_b, 2)

# Function to calculate 95% CI for Elo scores
def calculate_95_ci(elo, votes, z=1.96):
    if votes == 0:
        return Decimal(0), Decimal(0)
    elo = Decimal(elo)  # Ensure elo is a Decimal
    std_error = Decimal(400) / (Decimal(votes).sqrt())
    margin = Decimal(z) * std_error
    return round(elo - margin, 2), round(elo + margin, 2)

# Function to query leaderboard
def get_leaderboard():
    response = leaderboards_table.scan()
    leaderboard = response.get('Items', [])
    
    # Sort by EloScore in descending order
    leaderboard.sort(key=lambda x: x['EloScore'], reverse=True)
    
    return leaderboard
