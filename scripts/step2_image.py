LOG_PATH = "../attack_data/datasets/attack_techniques/T1003.001/atomic_red_team/windows-sysmon.log"

count = 0
with open(LOG_PATH, encoding="utf-8") as f:
    for line in f:
        if r"Name='Image'>C:\Windows\System32\rundll32.exe" in line and "<EventID>1</EventID>" in line:
            print (line)
            count += 1

print (f"Lines: {count}")
