savedcmd_nvmev.mod := printf '%s\n'   main.o pci.o admin.o io.o dma.o ssd.o conv_ftl.o pqueue/pqueue.o channel_model.o | awk '!x[$$0]++ { print("./"$$0) }' > nvmev.mod
