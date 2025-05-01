package workdone;
import java.util.*;

public class WordWrap {
    public static List<String> wrapText(String s, int k) {
        if (s == null || k <= 0) return null;

        List<String> result = new ArrayList<>();
        String[] words = s.split(" ");

        StringBuilder line = new StringBuilder();
        for (String word : words) {
            if (word.length() > k) {
                return null; // Cannot fit this word in any line
            }

            if (line.length() == 0) {
                line.append(word);
            } else if (line.length() + 1 + word.length() <= k) {
                line.append(" ").append(word);
            } else {
                result.add(line.toString());
                line = new StringBuilder(word);
            }
        }

        if (line.length() > 0) {
            result.add(line.toString()); // Add the last line
        }

        return result;
    }

    public static void main(String[] args) {
        String s = "the quick brown fox jumps over the lazy dog";
        int k = 10;

        List<String> wrapped = wrapText(s, k);
        if (wrapped == null) {
            System.out.println("Cannot wrap text.");
        } else {
            for (String line : wrapped) {
                System.out.println("\"" + line + "\"");
            }
        }
    }
}
