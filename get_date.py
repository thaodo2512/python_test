import subprocess
from datetime import datetime

def get_latest_commit_timestamp(file_path):
    # Get the latest commit timestamp for the file
    git_command = ['git', 'log', '-1', '--format=%cd', '--date=iso', file_path]
    result = subprocess.run(git_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    if result.returncode != 0:
        raise Exception(f"Error getting Git commit timestamp: {result.stderr}")
    
    # The timestamp is in ISO format, e.g., "2023-10-05 14:30:00 +0000"
    timestamp_str = result.stdout.strip()
    return timestamp_str

def parse_timestamp(timestamp_str):
    # Parse the timestamp string into a datetime object
    dt = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S %z")
    return dt

def generate_c_header(file_path, dt):
    # Extract year, month, day, hour, minute, second
    year = dt.year
    month = dt.month
    day = dt.day
    hour = dt.hour
    minute = dt.minute
    second = dt.second

    # Generate the C header content
    header_content = f"""\
#ifndef GIT_COMMIT_TIMESTAMP_H
#define GIT_COMMIT_TIMESTAMP_H

#define GIT_COMMIT_YEAR {year}
#define GIT_COMMIT_MONTH {month}
#define GIT_COMMIT_DAY {day}
#define GIT_COMMIT_HOUR {hour}
#define GIT_COMMIT_MINUTE {minute}
#define GIT_COMMIT_SECOND {second}

#endif // GIT_COMMIT_TIMESTAMP_H
"""

    # Write the content to the header file
    with open(file_path, 'w') as header_file:
        header_file.write(header_content)

def main():
    # Path to the file in the Git repository
    git_file_path = 'path/to/your/file.txt'  # Replace with your file path

    # Path to the output C header file
    header_file_path = 'git_commit_timestamp.h'

    try:
        # Get the latest commit timestamp
        timestamp_str = get_latest_commit_timestamp(git_file_path)
        
        # Parse the timestamp
        dt = parse_timestamp(timestamp_str)
        
        # Generate the C header file
        generate_c_header(header_file_path, dt)
        
        print(f"C header file generated successfully: {header_file_path}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
