package com.original.ncmdump;

import com.original.ncmdump.dump.NcmDump;
import org.junit.Test;

import java.io.File;

public class TestNcmDump {

    @Test
    public void test() {
        File file = new File("E:\\CloudMusic\\VipSongsDownload\\林子祥 - 男儿当自强.ncm");
        NcmDump ncmDump = new NcmDump(file);
        ncmDump.execute();
    }
}
