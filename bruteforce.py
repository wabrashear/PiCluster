from mpi4py import MPI
import time
import string
import sys

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()

# Parse password from CLI argument
if len(sys.argv) != 2:
    if rank == 0:
        print("Usage: python3 bruteforce.py <password>")
    sys.exit(1)

PASSWORD = sys.argv[1] if rank == 0 else None
PASSWORD = comm.bcast(PASSWORD, root=0)

if not PASSWORD:
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

found = False
progress_interval = 1000
found_global = False

for idx in range(start_index, end_index):
    # Periodically check if another rank found it
    if idx % progress_interval == 0 and not found:
        # Use non-blocking check across all ranks
        local_flag = 1 if found else 0
        global_flag = comm.allreduce(local_flag, op=MPI.SUM)
        if global_flag > 0:
            break

    guess = index_to_string(idx, CHARSET, LENGTH)
    if guess == PASSWORD:
        found = True
        print(f"[Rank {rank}] Found the password: {guess}")
        print(f"[Rank {rank}] Time taken: {time.time() - start_time:.4f} seconds")
        break

    if idx % progress_interval == 0:
        percent = ((idx - start_index) / (end_index - start_index)) * 100
        print(f"[Rank {rank}] Progress: {percent:.2f}%")

comm.Barrier()

if rank == 0:
    print(f"Search completed across {size} processes in {time.time() - start_time:.4f} seconds.")
