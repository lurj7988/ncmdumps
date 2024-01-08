package io.qaralotte.ncmdump;

import io.qaralotte.ncmdump.dump.NcmDump;
import io.qaralotte.ncmdump.utils.ErrorUtils;

import java.io.File;

public class Main {

    public static void main(String[] args) {
//        if (args.length == 0) {
//            ErrorUtils.error("No input .ncm File");
//        } else {
//            for (String arg : args) {
//                File file = new File(arg);
//                NcmDump ncmDump = new NcmDump(file);
//                ncmDump.execute();
//            }
//        }
        File file = new File("E:\\CloudMusic\\VipSongsDownload\\林子祥 - 男儿当自强.ncm");
        NcmDump ncmDump = new NcmDump(file);
        ncmDump.execute();
    }
}
