## bruteforce.py
from mpi4py import MPI
import time
import string
import sys

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()

# ----- USER CONFIG -----
try:
    PASSWORD = input("Enter the password to crack (fixed length): ").strip()
    if not PASSWORD:
        raise ValueError("Empty password")
except Exception as e:
    print(f"[Rank 0] Failed to get password input: {e}")
    sys.exit(1)


PASSWORD = comm.bcast(PASSWORD, root=0)

LENGTH = len(PASSWORD)

# Character set: uppercase, lowercase, digits, and special characters
CHARSET = string.ascii_letters + string.digits + "!@#$%^&*"

# ----- HELPER FUNCTION -----
def index_to_string(index, base_chars, length):
	chars = []
	base = len(base_chars)
	for _ in range(length):
		index, rem = divmod(index, base)
		chars.append(base_chars[rem])
	return ''.join(reversed(chars))

# ----- WORK DIVISION -----
start_time = time.time()

total_combinations = len(CHARSET) ** LENGTH
chunk_size = total_combinations // size
start_index = rank * chunk_size
end_index = start_index + chunk_size
if rank == size - 1:
	end_index = total_combinations  # Last rank covers any remainder

found = None
progress_interval = 100000  # Print progress every 100,000 guesses

# ----- MAIN SEARCH LOOP -----
for idx in range(start_index, end_index):
	# Cooperative check: has anyone found the password?
	found_flag = comm.allreduce(1 if found else 0, op=MPI.SUM)
	if found_flag > 0:
		break

	guess = index_to_string(idx, CHARSET, LENGTH)
	if guess == PASSWORD:
		found = guess
		print(f"[Rank {rank}] Found the password: {found}")
		total_time = time.time() - start_time
		print(f"[Rank {rank}] Time taken: {total_time:.4f} seconds")
		break

	# Progress printing every N guesses
	if idx % progress_interval == 0:
		percent = ((idx - start_index) / (end_index - start_index)) * 100
		print(f"[Rank {rank}] Progress: {percent:.2f}%")

comm.Barrier()

if rank == 0:
	total_time = time.time() - start_time
	print(f"Brute-force search completed across {size} processes in {total_time:.4f} seconds.")
