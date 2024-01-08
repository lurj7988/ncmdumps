package com.original.ncmdump;

import com.original.ncmdump.dump.NcmDump;
import com.original.ncmdump.utils.ErrorUtils;

import java.io.File;

public class Main {

    public static void main(String[] args) {
        if (args.length == 0) {
            ErrorUtils.error("No input .ncm File");
        } else {
            for (String arg : args) {
                File file = new File(arg);
                NcmDump ncmDump = new NcmDump(file);
                ncmDump.execute();
            }
        }
    }
}
