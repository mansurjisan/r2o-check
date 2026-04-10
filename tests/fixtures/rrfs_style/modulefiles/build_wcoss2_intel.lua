help([[Build environment for RRFS on WCOSS2]])

local pkgName = myModuleName()
local pkgVersion = myModuleVersion()

load("PrgEnv-intel/8.1.0")
load("intel/2022.1.2")
load("cray-mpich/8.1.9")
load("w3nco/2.4.1")
load("bacio/2.4.1")
