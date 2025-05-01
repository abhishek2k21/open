package CollectionWork;

import java.util.ArrayList;

public class CodeWork {
    public static void main(String[] args) {

        ArrayList<String> al = new ArrayList<>();

        al.add("Abdul");
        al.add("Rahim");
        al.add("Osama");
        al.add("Moshin");
        al.add("Faiz");
        al.add("Murshid");

        System.out.println(al);
        // System.out.println(al.get(0));
        // System.out.println(al.get(1));

        al.remove("Faiz");
        System.out.println(al.contains("Faiz"));
        System.out.println(al.size());
        al.set(2, "Maqbul");
        System.out.println(al.get(4));

    }

}
