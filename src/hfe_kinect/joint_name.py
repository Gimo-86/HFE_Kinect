import pykinect_azure as pykinect

# 獲取所有關節點名稱清單
joint_names = pykinect.K4ABT_JOINT_NAMES

print(f"{'Index':<10} | {'Joint Name':<20}")
print("-" * 35)

# 使用 enumerate 同時獲取索引與名稱
for index, name in enumerate(joint_names):
    print(f"{index:<10} | {name:<20}")