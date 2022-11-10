import matplotlib.pyplot as plt



f = open("read_vol_files.out", 'r')
lines = f.readlines()[1:]

n_49_469_1024 = 0
n_49_469_512 = 0
fovs_y=[]
fovs_z=[]
fovs_x=[]

for l in lines:
  n_y = int(l.split()[5])
  n_z = int(l.split()[6])
  n_x = int(l.split()[7])
  fov_y = float(l.split()[8])
  fov_z = float(l.split()[9])
  fov_x = float(l.split()[10])
  if n_y==49 and n_z==496 and n_x==1024:
    n_49_469_1024 +=1
  elif n_y==49 and n_z==496 and n_x==512:
    n_49_469_512 +=1
  elif n_y==49 and n_z==496 and not (n_x==1024 or n_x==512): # check if there are other n_x
    print(n_y, n_z, n_x)
  elif n_y==49 and not n_z==496: # check if there are other n_z
    print(n_y, n_z, n_x)
  elif not (n_y==49 or n_y==7): # check if there are other n_y
    print(n_y, n_z, n_x)

  if n_y==49:
    fovs_y.append(fov_y)
    fovs_z.append(fov_z)
    fovs_x.append(fov_x)


####### plot ######### 
plt.hist(fovs_y, bins=100)
plt.savefig("fov_y.png")
plt.xlim=[5,8]
plt.ylim=[5,8]

plt.hist(fovs_x, bins=100)
plt.savefig("fov_x.png")
plt.xlim=[5,8]
plt.ylim=[5,8]

plt.figure(figsize=(6,6))
plt.hist2d(fovs_x,fovs_y, bins=100)
plt.savefig("fov_xy.png")
plt.xlim=[5,8]
plt.ylim=[5,8]
