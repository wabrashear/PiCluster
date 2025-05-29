from mpi4py import MPI
import time
import string
import sys

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()

# Only rank 0 prompts for input
if rank == 0:
    print("Enter the password to crack (fixed length): ", end='', flush=True)
    try:
        PASSWORD = input().strip()
        if not PASSWORD:
            raise ValueError("Empty password entered")
    except Exception as e:
        print(f"[Rank 0] Error reading input: {e}")
        PASSWORD = None
else:
    PASSWORD = None

# Broadcast password to all ranks
PASSWORD = comm.bcast(PASSWORD, root=0)

if PASSWORD is None:
    if rank == 0:
        print("No valid password provided. Exiting.")
    sys.exit(1)

LENGTH = len(PASSWORD)
CHARSET = string.ascii_letters + string.digits + "!@#$%^&*"

def index_to_string(index, base_chars, length):
    chars = []
    base = len(base_chars)
    for _ in range(length):
        index, rem = divmod(index, base)
        chars.append(base_chars[rem])
    return ''.join(reversed(chars))

start_time = time.time()
total_combinations = len(CHARSET) ** LENGTH
chunk_size = total_combinations // size
start_index = rank * chunk_size
end_index = total_combinations if rank == size - 1 else start_index + chunk_size

found = None
progress_interval = 100000

for idx in range(start_index, end_index):
    if found:
        break
    if any(comm.allgather(found)):
        break

    guess = index_to_string(idx, CHARSET, LENGTH)
    if guess == PASSWORD:
        found = guess
        print(f"[Rank {rank}] Found the password: {found}")
        print(f"[Rank {rank}] Time taken: {time.time() - start_time:.4f} seconds")
        break

    if idx % progress_interval == 0:
        percent = ((idx - start_index) / (end_index - start_index)) * 100
        print(f"[Rank {rank}] Progress: {percent:.2f}%")

comm.Barrier()

if rank == 0:
    print(f"Search completed across {size} processes in {time.time() - start_time:.4f} seconds.")
